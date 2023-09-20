import os
import argparse
from mido import MidiFile
import keyboard
import time

octave_interval = 12
c3_pitch = 48
c5_pitch = 72
b5_pitch = 83
keytable = "a?s?df?g?h?j" + "q?w?er?t?y?u" + "1?2?34?5?6?7"
notetable = "C?D?EF?G?A?B"
play_state = 'idle'

def note_name(pitch):
    pitch_index = pitch % octave_interval
    if pitch_index < 0:
        return '-'
    pre = notetable[pitch_index]
    if pre == '?':
        pre = notetable[pitch_index - 1] + '#'
    return pre + str(pitch // octave_interval - 1)

def midi_playable(event):
    if event.is_meta or event.type != 'note_on':
        return False
    return True

def find_best_shift(midi_data):
    note_counter = [0] * octave_interval
    octave_list = [0] * 11

    for event in midi_data:
        if not midi_playable(event):
            continue
        for i in range(octave_interval):
            note_pitch = (event.note + i) % octave_interval
            if keytable[note_pitch] != '?':
                note_counter[i] += 1
                note_octave = (event.note + i) // octave_interval
                octave_list[note_octave] += 1

    max_note = max(range(len(note_counter)), key=note_counter.__getitem__)
    shifting = 0
    counter = 0

    for i in range(len(octave_list) - 3):
        amount = sum(octave_list[i: i + 3])

        if amount > counter:
            counter = amount
            shifting = i

    return int(max_note + (4 - shifting) * octave_interval)

def play(midi, shifting, speed):
    global play_state
    play_state = 'playing'

    for event in midi:
        if play_state != 'playing':
            break
        time.sleep(event.time / speed)
        if not midi_playable(event):
            continue
        pitch = event.note + shifting
        original_pitch = pitch

        if pitch < c3_pitch:
            pitch = pitch % octave_interval + c3_pitch
        elif pitch > b5_pitch:
            pitch = pitch % octave_interval + c5_pitch

        if pitch < c3_pitch or pitch > b5_pitch:
            continue

        key_press = keytable[pitch - c3_pitch]
        keyboard.send(key_press)

def control(midi, shifting, speed):
    global play_state
    if play_state == 'playing':
        play_state = 'pause'
    elif play_state == 'idle':
        keyboard.call_later(play, args=(midi, shifting, speed), delay=1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MIDI file auto player with Lyre in Genshin Impact')
    parser.add_argument('midi', nargs="?", type=str, help='path to MIDI file')
    parser.add_argument('--speed', type=float, default=1.0, help='adjust playback speed')
    args = parser.parse_args()
    midi = args.midi
    if not midi:
        midi = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'files/endless_love.mid')
    midi = MidiFile(midi)
    shifting = find_best_shift(midi)
    print("Press 'F5' to play/pause, and press 'Esc' to exit.\n")
    keyboard.add_hotkey('F5', lambda: control(midi, shifting, args.speed), suppress=True, trigger_on_release=True)
    keyboard.wait('Esc', suppress=True)
