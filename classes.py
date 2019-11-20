#!/usr/bin/env python3

"""
file: classes.py

Contains all abstract class definitions.
"""

from enum import Enum
from abc import ABC, abstractmethod
import re
from typing import Dict, List, Tuple, Union


class ParseMode(Enum):
    NORMAL = 0
    ORDER = 1
    SECTION = 2


class Song:
    """
    Class representing a single song, which consists of a current key, sections, and an ordering of sections with
    frequency. A Song instance represents both an instance of a song and a generator for chordsheets or slides.
    """
    def __init__(self, sections: Dict[str, "Section"], order: list, old_key: str):
        """
        :param sections: dictionary mapping section names (str) as keys to Section objects (Section)
        :param order: list(str, int) representing order of sections in song and frequency of each song
        :param old_key: str representing current key of sections
        """
        self.__sections = dict(sections)
        self.__order = list(order)
        self.__key = old_key

    def generate_chordsheet(self, new_key: str) -> str:
        """
        Create LaTeX chordsheet output of song in new key.
        :param new_key: str representing new key to output song in
        :return: str representing LaTeX chordsheet representation of song (without header info)
        """
        notes = Notes(self.__key, new_key)

        generated_sections = set()

        # generate output
        output = "\\bsong\n\n"
        for section_name, frequency in self.__order:  # generate section code per section
            output += self.__sections[section_name].generate_chordsheet(
                notes, frequency, repeated_section=section_name in generated_sections) + "\n\n"
            generated_sections.add(section_name)
        output += "\\esong\n\n"
        return output

    def generate_slides(self, repeat: bool=True) -> str:
        """
        Create LaTeX slides output of song in new key.
        :param repeat: bool representing whether to display slides which have previously been generated
        :return: str representing LaTeX slides representation of song (without header info)
        """
        generated_sections = set()
        first_slide = True

        # generate output
        output = ""
        for section_name, _ in self.__order:
            # generate slide code per section
            if (repeat or section_name not in generated_sections) and self.__sections[section_name].has_lyrics():
                output += self.__sections[section_name].generate_slides(first_slide) + "\n\n"
                first_slide = False
            generated_sections.add(section_name)
        return output

    def __str__(self):
        """
        :return: str representing song in human-friendly form
        """
        output = ""
        output += "Order:\n"
        output += "\n".join(f"{name} (x{frequency})" if frequency > 1 else name
                            for name, frequency in self.__order) + "\n\n"
        output += "\n\n".join(str(self.__sections[s]) for s in self.__sections)
        return output


class Section:
    """
    Class representing a section of music (e.g. Verse, Chorus, etc.), consisting of a sequence of musical or lyrical
    lines.
    """
    def __init__(self, name: str, lines: List["Line"]):
        """
        :param name: str representing name of section, used to reference section in ordering
        :param lines: List[Line] representing a list of Line objects, which could either be music or lyric lines.
        """
        self.name = name
        self.lines = list(lines)

    def get_wrapper(self, repeat: bool=False) -> Union[Tuple[str], str]:
        """
        Return begin and end sequence characters to wrap section in LaTeX chordsheet. Currently supported section
        names include Intro, Verse, Prechorus, Chorus, Break/Instrumental, Bridge, Outro, and Tag. A ValueError is thrown
        if the name cannot be parsed.
        :param repeat: bool representing whether this is a repeated section (in which case an abbreviated form of the
        tag is generated
        :return: Tuple[str] representing a tuple of
        """
        # check Regex matches for section name
        if re.match("^Intro$", self.name):
            return ("\\bi", "\\ei") if not repeat else "\\ri"
        elif re.match("^Verse( \\d)?$", self.name):
            return ("\\bv", "\\ev") if not repeat else "\\rv"
        elif re.match("^(Prechorus|Pre-chorus|Pre-Chorus)( \\d)?$", self.name):
            return ("\\bp", "\\ep") if not repeat else "\\rp"
        elif re.match("^Chorus( \\d)?$", self.name):
            return ("\\bc", "\\ec") if not repeat else "\\rc"
        elif re.match("^(Break|Instrumental)( \\d)?$", self.name):
            return ("\\bin", "\\ein") if not repeat else "\\rin"
        elif re.match("^Bridge( \\d)?$", self.name):
            return ("\\bb", "\\eb") if not repeat else "\\rb"
        elif re.match("^Outro$", self.name):
            return ("\\bo", "\\eo") if not repeat else "\\ro"
        elif re.match("^Tag( \\d)?$", self.name):
            return ("\\bt", "\\et") if not repeat else "\\rt"
        else:  # section name not parseable
            raise ValueError(self.name + " cannot be recognized as a valid section name.")

    def get_index(self) -> int:
        """
        Get index of section (e.g. 1 for "Verse 1", 2 for "Chorus 2", etc.)
        :return:
        """
        match = re.match("^([a-zA-Z]+) (\\d)$", self.name)
        if match:
            return int(match.group(2))
        else:
            return 1

    def has_lyrics(self) -> bool:
        """
        :return: True if at least one of its lines has lyrics, else False
        """
        for line in self.lines:
            if line.has_lyrics():
                return True
        return False

    def generate_chordsheet(self, notes: "Notes", frequency:int=1, repeated_section:bool=False) -> str:
        """
        Create LaTeX chordsheet output of section.
        :param notes: Notes instance representing transposition operator
        :param frequency: int representing number of times the section should be played
        :param repeated_section: bool - True if section has been played earlier in song, or False otherwise
        :return: str representing LaTeX chordsheet representation of section
        """
        # not a repeated section
        if not repeated_section:
            # build wrapper
            begin, end = self.get_wrapper(repeat=repeated_section)
            if frequency > 1:  # section is to be played more than once
                begin = "{}[{}]".format(begin, frequency, {})
            # build section representation
            return begin + "\n" + "\n\n".join(
                l.generate_chordsheet(notes) for l in self.lines) + "\n" + end
        # repeated section
        else:
            macro = self.get_wrapper(repeat=repeated_section)
            if frequency > 1:  # section is to be played more than once
                return "{0}[{2}]{{{1}}}".format(macro, self.get_index(), frequency, {})
            else:  # frequency == 1
                return "{0}{{{1}}}".format(macro, self.get_index(), {})

    def generate_slides(self, is_first_slide: bool) -> str:
        """
        Create LaTeX slides output of section.
        :param is_first_slide: True if slide being generated is the first slide, or False otherwise
        :return: str representing LaTeX slide representation of section
        """
        def create_slide(lines):
            output = ""
            if len(lines) > 0:
                output += "\\begin{frame}\n"
                output += "\\header\n"
                output += "\\begin{center}\n"
                output += "\n\n".join(line.get_lyrics() for line in lines)  # generate each line
                output += "\n\\end{center}\n"
                if is_first_slide:  # if first slide, include citation
                    output += "\\cite\n"
                output += "\\end{frame}"
            return output

        if not self.has_lyrics():
            raise RuntimeError("Error: cannot generate a slide for a section without lyrics.")

        output = ""
        lines_per_slide = []

        # collect lines
        for line in self.lines:
            if not line.is_break():
                lines_per_slide.append(line)
            else:
                output += create_slide(lines_per_slide)
                lines_per_slide = []
        output += create_slide(lines_per_slide)

        return output

    def __str__(self):
        """
        :return: str representing section in human-friendly form
        """
        output = self.name + ":\n"
        output += "\n".join(str(l) for l in self.lines)
        return output


class Line(ABC):
    """
    Abstract class representing a line of music, either as an instrumental line of chords or a lyric line with chords.
    """
    MAX_LENGTH = 52

    @staticmethod
    def parse(line: str) -> "Line":
        """
        Static method to parse a line of music to an instance of Line.
        :param line: str representing a line of music.
        :return: An instance of Line representing the appropriate type of music.
        """
        if MusicLine.is_music_line(line):
            return MusicLine.parse(line)  # parse chords-only line
        elif BreakLine.is_break_line(line):
            return BreakLine.parse(line)  # parse break line
        else:
            return Lyric.parse(line)  # parse lyrics line

    @abstractmethod
    def generate_chordsheet(self, notes: "Notes") -> str:
        """
        Create LaTeX chordsheet output of line in new key.
        :param notes: Notes object used to transpose line to proper chords
        :return: str representing LaTeX chordsheet representation of line
        """
        pass

    @abstractmethod
    def has_lyrics(self) -> bool:
        """
        :return: True if Line has lyrics, i.e. should be printed on slide, or False otherwise
        """
        pass

    @abstractmethod
    def get_lyrics(self) -> str:
        """
        :return: str representing lyrics without any chords
        """
        pass

    @abstractmethod
    def is_break(self) -> bool:
        """
        :return: True if a break line
        """
        pass

    @abstractmethod
    def __str__(self):
        """
        :return: str representing line in human-friendly form
        """
        pass


class BreakLine(Line):
    """
    Class representing a break in slides, of the form

    ---

    """
    def generate_chordsheet(self, notes: "Notes") -> str:
        return ""

    @staticmethod
    def parse(line: str) -> Line:
        return BreakLine()

    def has_lyrics(self) -> bool:
        return False

    def get_lyrics(self) -> str:
        return ""  # has no lyrics

    @staticmethod
    def is_break_line(line: str) -> bool:
        """
        :param line: str representing a line in the raw chordsheet
        :return: True if the line is a break line
        """
        return re.match("(-)*$", line) is not None

    def is_break(self) -> bool:
        return True

    def __str__(self):
        return "---"


class MusicLine(Line):
    """
    Class representing a line of music, e.g. of the form

    | G    | Em    | C     | D     |

    """
    def __init__(self, measures: List[List["Chord"]]):
        """
        Create an instance of a music line with specified measures
        :param measures: List of lists of Chord instances, where each sub-list represents one measure
        """
        self.measures = list(measures)

    def generate_chordsheet(self, notes: "Notes") -> str:
        return "| " + " | ".join(
            " ".join(Chord.convert(notes.transpose(chord)) for chord in m) for m in self.measures) + " |"

    @staticmethod
    def is_music_line(line: str) -> bool:
        """
        :param line: str representing a line in the raw chordsheet
        :return: True if the line is a music-only line
        """
        return re.match("^\|:?([A-Ga-z0-9#/ ]+:?\|)+( \(x(\d)+\))?$", line) is not None  # match measures

    @staticmethod
    def parse(line: str) -> Line:
        measures = []
        line_split = line.split("|")
        for m in line_split[1:]:  # skip first empty measure
            if m == "\n":  # skip newline measure at end
                pass
            elif "/" in m:  # '/' separates chords; split on spaces and apply chord to each
                measures.append(list(map(Chord, m.split(" "))))
            else:  # append single chord
                measures.append([Chord(m.strip())])
        return MusicLine(measures)

    def has_lyrics(self) -> bool:
        return False

    def get_lyrics(self) -> str:
        return ""  # has no lyrics

    def is_break(self) -> bool:
        return False

    def __str__(self):
        return "| " + " | ".join(" ".join(str(token) for token in m) for m in self.measures) + " |"


class Lyric(Line):
    """
    Class representing a single lyric line, possibly including chords.
    """
    def __init__(self, characters: List["Character"]):
        """
        :param characters: List of Character instances
        """
        self.characters = list(characters)

    @staticmethod
    def parse(line: str) -> Line:
        line_tokens = []
        i = 0
        line = line.rstrip()
        while i < len(line):  # iterate through characters of line
            if line[i] == "[":  # parse chord
                start_chord = i + 1
                if i >= len(line):  # hit end of line
                    raise ValueError("Error: found unparseable line; couldn't find end to chord.")

                while line[i] != "]":  # look for end of chord
                    i += 1
                    if i >= len(line):
                        raise ValueError("Error: found unparseable line; couldn't find end to chord.")
                end_chord = i
                i += 1

                if i >= len(line) or line[i] == "[":  # hit end of line or found new chord
                    line_tokens.append(Character("", Chord(line[start_chord:end_chord])))
                else:  # apply chord to next character
                    line_tokens.append(Character(line[i], Chord(line[start_chord:end_chord])))
                    i += 1
            else:  # non-chord character
                line_tokens.append(Character(line[i]))
                i += 1

        return Lyric(line_tokens)

    def has_lyrics(self) -> bool:
        return True

    def get_lyrics(self) -> str:
        return "".join(c.get_char() for c in self.characters)

    def generate_chordsheet(self, notes: "Notes") -> str:
        # initialization
        output = ""
        characters_since_chord = 0
        len_last_chord = None
        total_len = 0

        for c in self.characters:  # iterate through characters in line
            if c.has_chord():  # character has chord
                # add whitespace between consecutive chords if necessary
                if len_last_chord is not None and characters_since_chord <= len_last_chord:
                    output += "\\spv{{{0}}}".format(len_last_chord - characters_since_chord + 1)
                    total_len += len_last_chord - characters_since_chord + 1

                # reset
                characters_since_chord = 0
                len_last_chord = c.get_len_transposed_chord(notes)

            characters_since_chord += 1
            output += c.generate_chordsheet(notes)  # generate representation of character and chord
            total_len += 1

        # update total length
        if len_last_chord is not None:
            total_len += max(0, len_last_chord - characters_since_chord)

        # fit line to LaTeX column width
        if total_len > Line.MAX_LENGTH:
            return "\\fit{" + output + "}"
        else:
            return output

    def is_break(self) -> bool:
        return False

    def __str__(self):
        return "".join(str(c) for c in self.characters)


class Character:
    """
    Class representing a single character, possibly with a chord
    """
    def __init__(self, c: str, chord: "Chord"=None):
        """
        :param c: str representing a single character or empty string
        :param chord: Chord representing a chord, to be played at that character
        """
        assert len(c) <= 1  # should be at most length 1, since it is a character
        self.char = c
        self.chord = chord

    def get_char(self) -> str:
        """
        :return: str representing character represented by instance
        """
        return self.char

    def has_chord(self) -> bool:
        """
        :return: True if instance has chord, or False otherwise
        """
        return self.chord is not None

    def generate_chordsheet(self, notes: "Notes") -> str:
        """
        Create LaTeX chordsheet output of character, with chord if existing.
        :param notes: Notes object used to transpose chord
        :return: str representing LaTeX chordsheet representation of character and chord
        """
        return self.char if not self.has_chord() else self.chord.generate_chordsheet(notes) + self.char

    def get_len_transposed_chord(self, notes: "Notes") -> int:
        if self.has_chord():
            return len(notes.transpose(self.chord))

    def __str__(self):
        """
        :return: str representing character and chord in human-friendly form
        """
        return self.char if not self.has_chord() else "[" + str(self.chord) + "]" + self.char


class Chord:
    def __init__(self, chord: str):
        """
        :param chord: str representing chord
        """
        self.chord = chord

    @staticmethod
    def convert(chord: str) -> str:
        """
        convert chord from music text notation to LaTeX notation, i.e. change "#" to "\s "
        :param chord: str representing chord in music text notation
        :return: chord in LaTeX notation.
        """
        new_chord = ""
        for i in range(len(chord)):
            # convert sharp ("#") to "\s " or otherwise preserve character of chord
            new_chord += chord[i] if chord[i] != "#" else "\\s "
        return new_chord

    def generate_chordsheet(self, notes: "Notes") -> str:
        """
        Create LaTeX chordsheet output of chord.
        :param notes: Notes object used to transpose chord
        :return: str representing LaTeX chordsheet representation of chord
        """
        return "\c{" + Chord.convert(notes.transpose(self)) + "}"

    def __getitem__(self, index: int) -> str:
        """
        :param index: int representing position to index into chord
        :return: str representing (index)th character of chord
        """
        return self.chord[index]

    def __len__(self) -> int:
        """
        :return: int representing length of chord
        """
        return len(self.chord)

    def __str__(self):
        """
        :return: str representing chord
        """
        return self.chord


class Notes:
    """
    Class representing a transposition class from one key to another. When Notes instance is defined, keys are
    configured with the object, and the old and new keys are used to transpose notes or chords appropriately.

    Transposition occurs by maintaining internal representations of sharp and flat keys.
    """
    notes_sharp = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    notes_flat = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "Cb"]

    assert len(notes_sharp) == len(notes_flat)

    sharp_keys = {"C", "G", "D", "A", "E", "B", "F#", "C#", "G#", "D#", "A#"}
    flat_keys = {"F", "Bb", "Eb", "Ab", "Db", "Gb"}

    def __init__(self, input_key: str, output_key: str):
        """
        Generates Notes object based on input and output keys.
        :param input_key: str representing input key, as a single letter and denotation of sharp (#) or flat (b).
        :param output_key: str representing output key, as a single letter and denotation of sharp (#) or flat (b).
        """
        # store input key based on internal representation
        if Notes.is_sharp_key(input_key):
            self.__input_notes = Notes.notes_sharp
        elif Notes.is_flat_key(input_key):
            self.__input_notes = Notes.notes_flat
        else:
            raise ValueError(str(input_key) + " not supported in Notes constructor input type.")

        # store output key based on internal representation
        if Notes.is_sharp_key(output_key):
            self.__output_notes = Notes.notes_sharp
        elif Notes.is_flat_key(output_key):
            self.__output_notes = Notes.notes_flat
        else:
            raise ValueError(str(output_key) + " not supported in Notes constructor for output type.")

        self.__semitones_up = self.__get_semitones_up(input_key, output_key)

    @staticmethod
    def is_sharp_key(key: str) -> bool:
        """
        :param key: str representing key to check.
        :return: True if key is among sharp keys, or False otherwise.
        """
        return key in Notes.sharp_keys

    @staticmethod
    def is_flat_key(key: str) -> bool:
        """
        :param key: str representing key to check.
        :return: True if key is among flat keys, or False otherwise.
        """
        return key in Notes.flat_keys

    def __get_semitones_up(self, old_key: str, new_key: str) -> int:
        """
        Get number of semitones to move from old key to new key. Positive denotes that the new key is higher, and
        negative denotes that the new key is lower.
        :param old_key: str representing input key, as a single letter and denotation of sharp (#) or flat (b).
        :param new_key: str representing output key, as a single letter and denotation of sharp (#) or flat (b).
        :return: int representing number of semitones to translate notes up
        """
        return (self.__output_notes.index(new_key) - self.__input_notes.index(old_key)) % len(self.__output_notes)

    def __transpose(self, note: str) -> str:
        """
        Transpose a single note by the stored semitones up.
        :param note: str representing a note to be transposed, where the note should be among the internal input notes
        (sharp or flat based on the input key).
        :return: str representing the note after it is transposed
        """
        index = self.__input_notes.index(note)  # index of old note
        return self.__output_notes[(index + self.__semitones_up) % len(self.__output_notes)]

    def transpose(self, chord: Chord) -> str:
        """
        Transpose a chord by the stored semitones up.
        :param chord: str representing a chord to be transposed
        :return: str representing the chord after it is transposed
        """
        new_chord = ""
        i = 0
        while i < len(chord):  # iterate through chord
            if chord[i] in "ABCDEFG":  # base note of chord
                if i + 1 < len(chord) and chord[i + 1] in {"#", "b"}:  # transpose note with proceeding sharp or flat
                    new_chord += self.__transpose(chord[i:i + 2])
                    i += 2
                else:  # transpose note on its own
                    new_chord += self.__transpose(chord[i])
                    i += 1
            else:  # transfer character over to new chord without transposition (e.g. any of "maj7" in "Gmaj7")
                new_chord += chord[i]
                i += 1
        return new_chord
