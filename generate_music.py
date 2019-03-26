#!/usr/bin/env python3

"""
file: generate_music.py

Main script to generate chordsheets and slides from a raw textfile. Please view the README for installation and usage
instructions.
"""

import os
import sys
from string import Template
from subprocess import run
import requests
from pprint import pprint
import shutil
from utils.headers import CHORDSHEET_HEADER, SLIDES_HEADER
from utils.classes import *

# Global constants
MAX_COMPOSER_FIELD_LENGTH = 40
DEFAULT_KEY = "C"
CONFIG_FILENAME = "CONFIGURATION"
CCLI_LOGIN_URL = "https://profile.ccli.com/account/signin?appContext=SongSelect&returnUrl=https%3a%2f%2fsongselect.ccli.com%2f"

DEFAULT_HEADER = {
    "composer": "Unknown Artist",
    "ccli": "N/A",
    "bpm": "Unknown",
    "signature": "Unknown signature",
    "verse": "N/A",
    "arranger": "Unknown Arranger",
    "year": "",
    "publisher": "Unknown Publisher"
}

# Regex strings
SONG_TAG_REGEX = "^<song> ([a-zA-Z0-9 :,'()/-]+)$"
CCLI_TAG_REGEX = "^<ccli> ([0-9/ ]+|N/A)$"
COMPOSER_TAG_REGEX = "^<composer> ([a-zA-Z0-9 ,-.]+)$"
KEY_TAG_REGEX = "^<key> ([A-G][#b]? major|minor)$"
BPM_TAG_REGEX = "^<bpm> ((?:[0-9]+)|\?)$"
SIGNATURE_TAG_REGEX = "^<signature> ((?:[0-9]+/[0-9]+)|\?)"
VERSE_TAG_REGEX = "^<verse> ([a-zA-Z0-9 :,-]+|N/A)$"
ARRANGER_TAG_REGEX = "^<arranger> ([a-zA-Z0-9 -]+)$"
PUBLISHER_TAG_REGEX = "^<publisher> ([a-zA-Z0-9 ,.!'/-]+|N/A)$"
YEAR_TAG_REGEX = "^<year> ([0-9]+|N/A)$"
ARTIST_CCLI_REGEX = r"<ul class=\"authors\">[a-zA-Z0-9 '\/\n\r?=_\"<>-]+<\/ul>"
GET_ARTISTS_REGEX = r"<a href=[a-zA-Z0-9 '\/?=_\"-]+>([a-zA-Z '-]+)<\/a>\r\n[ ]*"
YEAR_CCLI_REGEX = r"<ul class=\"song-meta-list\">\r\n[ ]*<li>Copyrights<\/li>\r\n[ ]*[a-zA-Z0-9 !'\/\n\r?=_\"<>-]+<\/ul>"
GET_YEAR_REGEX = r"<li>([0-9]+) [a-zA-Z0-9 ]+<\/li>"
PUBLISHER_CCLI_REGEX = r"<ul class=\"song-meta-list\">\r\n[ ]*<li>Copyrights<\/li>\r\n[ ]*[a-zA-Z0-9 !'\/\n\r?=_\"<>-]+<\/ul>"
GET_PUBLISHERS_REGEX = r"<li>[0-9 ]*([a-zA-Z0-9 !]+)<\/li>"


def p_warning(*args):
    """
    Print to console with a warning tag
    :param args: args to print call.
    :return: None
    """
    print("[WARNING]", *args)

def get_variables(filename: str):
    """
    Parses configuration file, in particular looking for
    - input_directory = the path to the directory containing the input raw chordsheet
    - chordsheets_output_directory = the path to the directory in which the final chordsheet should be saved
    - slides_output_directory = the path to the directory in which the final slides should be saved
    - ccli_email_address = the email address to be used for the CCLI account (optional)
    - ccli_password = the password to be used for the CCLI account (optional)
    The file expects a format such as

        variable=value

    For example:

        input_directory=chordsheets_raw
        chordsheets_output_directory=chordsheets_final
        slides_output_directory=slides
        ccli_email_address=emailaddress@domain.com
        ccli_password=yourpasswordhere

    :param filename: str representing path to configuration file
    :return:
    """
    directories = {"input": "", "output": {"chordsheets": "", "slides": ""}}
    account_info = {}
    with open(filename, "r") as f:
        for line in f.readlines():
            if "=" in line:
                name, value = line.split("=")
                value = value.rstrip()
                if name == "input_directory":
                    directories["input"] = value
                elif name == "chordsheets_output_directory":
                    directories["output"]["chordsheets"] = value
                elif name == "slides_output_directory":
                    directories["output"]["slides"] = value
                elif name == "ccli_email_address":
                    account_info["EmailAddress"] = value
                elif name == "ccli_password":
                    account_info["Password"] = value
    return directories, account_info


def parse(filename: str):
    """
    Main function for parsing a raw chordsheet, including parsing the header information, the section order, and the
    chords and lyrics themselves.
    :param filename: str representing name of raw chordsheet file
    :return: list representing [header data (dict), instance of a Song (Song)]
    """
    def verify_data(header_data: dict):
        """
        Checks for minimal data found in header. If no song title or key is found, an error will be thrown.
        :param header_data: dict representing the header data, with tags stored as keys
        :return: True if successful
        """
        if "song" not in header_data:
            raise ValueError("File must include a song title, but no <song> tag was found.")
        if "major_minor" not in header_data:
            raise ValueError("File must include a key, but no <key> tag was found.")
        return True

    # initialize variables
    header_data = dict(DEFAULT_HEADER)
    sections = {}
    lines = []
    order = []
    old_key = DEFAULT_KEY
    section_name = None

    # read file
    with open(filename, "r") as f:
        MODE = ParseMode.NORMAL  # initialize mode
        content = f.readlines()

        # iterate through lines
        for l in content:
            # NORMAL mode
            if MODE == ParseMode.NORMAL:
                # check header
                # <song>
                if re.match(SONG_TAG_REGEX, l):
                    header_data["song"] = re.match(SONG_TAG_REGEX, l).group(1)
                # <ccli>
                elif re.match(CCLI_TAG_REGEX, l):
                    header_data["ccli"] = re.match(CCLI_TAG_REGEX, l).group(1)
                # <composer> (i.e. artist)
                elif re.match(COMPOSER_TAG_REGEX, l):
                    header_data["composer"] = re.match(COMPOSER_TAG_REGEX, l).group(1)
                # <key> (of raw chordsheet)
                elif re.match(KEY_TAG_REGEX, l, re.IGNORECASE):
                    key_info = re.match(KEY_TAG_REGEX, l, re.IGNORECASE).group(1)
                    old_key = key_info.split(" ")[0]
                    header_data["major_minor"] = key_info.split(" ")[1]
                    if header_data["major_minor"].lower() == "major":
                        header_data["major_minor"] = "Major"
                # <bpm>
                elif re.match(BPM_TAG_REGEX, l):
                    header_data["bpm"] = int(re.match(BPM_TAG_REGEX, l).group(1))
                # <signature> (e.g. 4/4, 6/8)
                elif re.match(SIGNATURE_TAG_REGEX, l):
                    header_data["signature"] = re.match(SIGNATURE_TAG_REGEX, l).group(1)
                # <verse>
                elif re.match(VERSE_TAG_REGEX, l):
                    header_data["verse"] = re.match(VERSE_TAG_REGEX, l).group(1)
                # <arranger>
                elif re.match(ARRANGER_TAG_REGEX, l):
                    header_data["arranger"] = re.match(ARRANGER_TAG_REGEX, l).group(1)
                # <publisher>
                elif re.match(PUBLISHER_TAG_REGEX, l):
                    header_data["publisher"] = re.match(PUBLISHER_TAG_REGEX, l).group(1)
                # <year>
                elif re.match(YEAR_TAG_REGEX, l):
                    header_data["year"] = re.match(YEAR_TAG_REGEX, l).group(1)

                # switch to ORDER mode
                elif re.match("^<order>", l):
                    MODE = ParseMode.ORDER

                # switch to SECTION mode
                elif re.match("^<([a-zA-Z0-9 ]+)>$", l):
                    MODE = ParseMode.SECTION
                    lines = []
                    section_name = re.match("^<([a-zA-Z0-9 ]+)>", l).group(1)

            # ORDER mode
            elif MODE == ParseMode.ORDER:
                if l == "\n":  # terminal character
                    MODE = ParseMode.NORMAL
                else:  # parse ordering of sections
                    match = re.match("^([a-zA-Z0-9 ]+?)( \(x?(\\d)+x?\))?$", l)
                    name = match.group(1)
                    frequency = int(match.group(3)) if match.group(3) is not None else 1
                    order.append((name, frequency))

            # SECTION mode
            elif MODE == ParseMode.SECTION:
                if l == "\n":  # terminal character
                    MODE = ParseMode.NORMAL
                    sections[section_name] = (Section(section_name, lines))
                    section_name = None
                else:  # collect lines to be parsed by Section constructor later
                    lines.append(Line.parse(l))

        if MODE == ParseMode.SECTION:  # section ended without sole newline
            sections[section_name] = (Section(section_name, lines))

    verify_data(header_data)  # verify that the header data has the minimal amount needed to generate the song

    return header_data, Song(sections, order, old_key)


def supplement_header(header: dict, account_info: dict):
    """
    If information is missing from the header, make a GET request to CCLI to complete the missing information.
    :param header: dict representing header info, with tags as keys. header must contain a CCLI number in order to make
    the request.
    :param account_info: dict representing account info for CCLI, of the form

        {"EmailAddress": <email_address>, "Password": <password>}

    If the dictionary does not have one of these, the script will prompt the user for entry during execution.
    :return: dict representing new header
    """

    def parse_artist(html_text: str) -> str:
        """
        Parse html response for artist names.
        :param html_text: str representing html of CCLI page for song.
        :return: str representing artist names, delimited by commas
        """
        # parse HTML for artists
        m = re.search(ARTIST_CCLI_REGEX, html_text, re.M)
        if m is not None:
            artists = re.findall(GET_ARTISTS_REGEX, m.group(0), re.M)
            if len(artists) > 0:  # artists found
                return ", ".join(artists)
            else:  # general tags found, but no artists parsed
                p_warning("author tags found, but composer not extracted in GET request.")
                return DEFAULT_HEADER["composer"]
        p_warning("composer not found in GET request.")
        return DEFAULT_HEADER["composer"]

    def parse_year(html_text: str) -> int:
        """
        Parse html response for publishing year.
        :param html_text: str representing html of CCLI page for song.
        :return: int representing year
        """
        # parse HTML for year
        m = re.search(YEAR_CCLI_REGEX, html_text, re.M)
        if m is not None:
            match_year = re.search(GET_YEAR_REGEX, m.group(0), re.M)
            if match_year is not None:  # year found
                return int(match_year.group(1))
            else:  # general tags found, but no copyright year parsed
                p_warning("copyright found, but no year listed in GET request.")
                return int(DEFAULT_HEADER["year"])
        p_warning("no copyright tag found in GET request.")
        return int(DEFAULT_HEADER["year"])

    def parse_publisher(html_text: str) -> str:
        """
        Parse html response for publishers.
        :param html_text: str representing html of CCLI page for song.
        :return: str representing names of publishers
        """
        # parse HTML for publisher
        m = re.search(PUBLISHER_CCLI_REGEX, html_text, re.M)
        if m is not None:
            publishers = re.findall(GET_PUBLISHERS_REGEX, m.group(0), re.M)
            if len(publishers) > 0:  # publisher found
                return ", ".join(publishers[1:])
            else:  # general tag found, but no publishers parsed
                p_warning("copyright found, but publishers not extracted in GET Request")
                return DEFAULT_HEADER["publisher"]
        p_warning("no copyright tag found in GET request.")
        return DEFAULT_HEADER["publisher"]

    new_header = dict(header)

    # check if a request should be initiated to the CCLI website
    if (new_header["composer"] != "Unknown Artist" and
            new_header["year"] != "" and
            new_header["publisher"] != "Unknown Publisher"):  # composer, year, and publisher already set
        return new_header
    elif "ccli" not in header or header["ccli"] == "N/A":  # no CCLI number
        p_warning("no CCLI provided, so skipping lookup...")
        return new_header

    # Initiate request
    with requests.Session() as s:
        print("Initiating GET request...")

        # check if account info is already loaded
        if "EmailAddress" not in account_info:
            account_info["EmailAddress"] = input("Enter CCLI email address (to skip, press enter):")
            if len(account_info["EmailAddress"]) == 0:
                return new_header

        if "Password" not in account_info:
            account_info["Password"] = input("Enter CCLI password (to skip, press enter):")
            if len(account_info["Password"]) == 0:
                return new_header

        s.post(CCLI_LOGIN_URL, account_info)  # login

        # make request to CCLI page for song
        url = "https://songselect.ccli.com/songs/{}".format(header["ccli"])
        headers = {'Accept-Encoding': 'identity'}
        r = s.get(url, headers=headers)

        # debugging
        # with open("post_response.txt", "w") as f:
        #     f.write(repr(r.text))

        # parse HTML response for fields missing information
        if new_header["composer"] == "Unknown Artist":
            new_header["composer"] = parse_artist(r.text)

        if new_header["year"] == "":
            new_header["year"] = parse_year(r.text)

        if new_header["publisher"] == "Unknown Publisher":
            new_header["publisher"] = parse_publisher(r.text)

    return new_header


def generate_chordsheet_header(header) -> str:
    """
    Returns header with substituted values given by header.
    :param header: a dictionary of tags to values, as provided by input text file. Expected fields include
      "song" - name of song
      "ccli" - CCLI number
      "composer" - name(s) of composer(s) (max 40 characters)
      "key" - key of song
      "bpm" - recommended BPM of song
      "signature" - time signature of song (e.g. 4/4)
      "verse" - Bible verse(s) associated with song
      "arranger" - name(s) of arranger(s)
    :return: string representing header with substituted values
    """
    if len(header["composer"]) > MAX_COMPOSER_FIELD_LENGTH:  # abbreviate composer
        composers = header["composer"].split(",")
        header["composer"] = composers[0].strip() + " et. al."
        assert len(header["composer"]) <= MAX_COMPOSER_FIELD_LENGTH

    # generate template and substitute
    header_template = Template(CHORDSHEET_HEADER)
    return header_template.substitute(header)


def generate_slides_header(header) -> str:
    """
    Returns header with substituted values given by header.
    :param header: a dictionary of tags to values, as provided by input text file. Expected fields include
      "song" - name of song
      "ccli" - CCLI number
      "composer" - name(s) of composer(s)
      "year" - year song was published
      "publisher" - list of publishers of song
    :return: string representing header with substituted values
    """
    # check that all fields are present
    assert "song" in header and "ccli" in header and "composer" in header and "year" in header and "publisher" in header

    # generate template and substitute
    header_template = Template(SLIDES_HEADER)
    return header_template.substitute(header)


def generate_chordsheet(song: Song, new_key:str=DEFAULT_KEY) -> str:
    """
    Returns string representation of generated LaTeX chordsheet in new key.
    :param song: Song object representing song for which to generate chordsheet
    :param new_key: str representing new key in which to output chordsheet
    :return: str representing non-header content of chordsheet output in LaTeX
    """
    return song.generate_chordsheet(new_key)


def generate_slides(song: Song) -> str:
    """
    Returns string representation of generated LaTeX slides.
    :param song: Song object representing song for which to generate slides.
    :return: str representing non-header content of slide output in LaTeX
    """
    return song.generate_slides()


def get_chordsheet_destination(path: str, root_filename: str, new_key: str) -> str:
    """
    Generate path at which to save chordsheet.
    :param path: str representing root path
    :param root_filename: str representing root filename
    :param new_key: str representing new key
    :return: str representing path to output LaTeX chordsheet file
    """
    return os.path.join(path, root_filename + " - " + new_key + ".tex")


def get_slides_destination(path: str, root_filename: str) -> str:
    """
    Generate path at which to save slides.
    :param path: str representing root path
    :param root_filename: str representing root filename
    :return: str representing path to output LaTeX slides file
    """
    return os.path.join(path, root_filename + " - slides.tex")


def write_chordsheet(destination: str, header: str, chordsheet: str):
    """
    Write LaTeX chordsheet to file.
    :param destination: str representing path to output LaTeX file
    :param header: str representing header info for LaTeX chordsheet
    :param chordsheet: str representing non-header body of LaTeX chordsheet
    :return: True if successful
    """
    with open(destination, "w") as f:
        f.write(header + "\n")
        f.write("\\begin{document}\n")
        f.write(chordsheet)
        f.write("\\end{document}\n")
    return True


def write_slides(destination, header: str, chordsheet: str):
    """
    Write LaTeX slides to file.
    :param destination: str representing path to output LaTeX file
    :param header: str representing header info for LaTeX slides
    :param chordsheet: str representing non-header body of LaTeX slides
    :return: True if successful
    """
    with open(destination, "w") as f:
        f.write(header + "\n")
        f.write("\\begin{document}\n")
        f.write(chordsheet)
        f.write("\\end{document}\n")
    return True


def compile(root_filename: str, chordsheet_file: str, slides_file: str):
    """
    Run command-line tools to generate PDFs and PNGs of chordsheet and slides. Runs

    pdflatex --interaction=nonstopmode <chordsheet_file>.tex
    pdflatex --interaction=nonstopmode <slides_file>.tex
    convert -verbose -density 300 -geometry 1920x1080 <slides_file>.pdf -quality 100 -sharpen 0x1.0 <slides_file>.png

    :param root_filename: str representing root filename
    :param chordsheet_file: str representing the path to the LaTeX chordsheet file, to be compiled into a PDF
    :param slides_file: str representing the path to the LaTeX slides file, to be compiled into a PDF and PNGs
    """
    # generate chordsheet and slide files
    run(["pdflatex", "--interaction=nonstopmode", chordsheet_file])
    run(["pdflatex", "--interaction=nonstopmode", slides_file])

    # generate slide pngs
    if shutil.which("convert"):  # convert command exists
        slides_basename = slides_file.rpartition(".")[0]
        output_directory = os.path.join(os.path.dirname(slides_file), root_filename)

        if os.path.isdir(output_directory):
            shutil.rmtree(output_directory)  # remove individual slide output
        os.makedirs(output_directory)  # create directory

        output_png = os.path.join(output_directory, f"{root_filename}.png")

        # execute convert command
        run(["convert",
             "-verbose",
             "-density", "300",
             "-geometry", "1920x1080",
             f"{slides_basename}.pdf",
             "-quality", "100",
             "-sharpen", "0x1.0",
             f"{output_png}"])
    else:
        print("-------")
        p_warning("Convert function not found. No individual slides were generated.")

def clean(directory: str, chordsheet_filename: str, slides_filename: str, destination_directories: dict):
    """
    Remove unnecessary files and move files as needed.
    :param directory: str representing path to directory containing all intermediately generated files
    :param chordsheet_filename: str representing path to chordsheet file
    :param slides_filename: str representing path to slides file
    :param destination_directories: dict representing desired directories in which to store chordsheets and slides
    """
    # get base filename
    chordsheet_filename_without_ext = str(os.path.basename(chordsheet_filename).rpartition(".")[0])
    slides_filename_without_ext = str(os.path.basename(slides_filename).rpartition(".")[0])

    # move PDFs to destination directories
    os.rename(chordsheet_filename_without_ext + ".pdf",
              os.path.join(destination_directories["output"]["chordsheets"], chordsheet_filename_without_ext + ".pdf"))
    os.rename(slides_filename_without_ext + ".pdf",
              os.path.join(destination_directories["output"]["slides"], slides_filename_without_ext + ".pdf"))

    # remove auxiliary files
    pattern = re.compile("^(" + chordsheet_filename_without_ext + "|" + slides_filename_without_ext + ")\.[^.]+$")
    for f in os.listdir(directory):
        if pattern.match(f):
            os.remove(os.path.join(directory, f))

if __name__ == '__main__':
    # parse command line
    if len(sys.argv) < 3:
        print("Usage:"
              "\n  python3 generate_music.py <path_to_chordsheet> <new_key>"
              "\n  python3 generate_music.py <path_to_chordsheet> <old_key> <new_key>", file=sys.stderr)
        sys.exit(1)

    path_to_chordsheet = sys.argv[1]
    if len(sys.argv) >= 4:
        old_key = sys.argv[2]
        new_key = sys.argv[3]
    else:
        old_key = DEFAULT_KEY
        new_key = sys.argv[2]

    root_filename = path_to_chordsheet.rpartition(".")[0]

    # parse config file
    directories, account_info = get_variables(CONFIG_FILENAME)

    # generate chordsheet
    header_info, song = parse(os.path.join(directories["input"], path_to_chordsheet))
    header_info["key"] = new_key + " " + header_info["major_minor"]  # change to new key passed in command-line
    header_info = supplement_header(header_info, account_info)

    # have user confirm that header info looks correct
    print("Header Info:")
    pprint(header_info)
    input("Hit enter to start.")

    # generate chordsheet
    chordsheet_header = generate_chordsheet_header(header_info)
    chordsheet = generate_chordsheet(song, new_key=new_key)

    # generate slides
    slides_header = generate_slides_header(header_info)
    slides = generate_slides(song)

    # write to tex file and compile
    chordsheet_file = get_chordsheet_destination(directories["output"]["chordsheets"], root_filename, new_key)
    write_chordsheet(chordsheet_file, chordsheet_header, chordsheet)

    slides_file = get_slides_destination(directories["output"]["slides"], root_filename)
    write_slides(slides_file, slides_header, slides)

    # produce output files
    compile(root_filename, chordsheet_file, slides_file)
    clean(os.path.dirname(os.path.abspath(path_to_chordsheet)), chordsheet_file, slides_file, directories)
