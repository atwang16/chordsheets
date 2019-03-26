# Chordsheets Project
This project provides users with the ability to generate chordsheets and slides from a single text file, specifically
intended for Christian worship chordsheets. The benefits of using such a project include the following:

* Creation of chordsheets in a human-friendly and computer-parsible format
* Generation of clean, well-formatted chordsheets in any desired key
* Generation of slides, both as PDFs and separate PNGs, from the same file, ensuring consistent lyrics between the two
* Formatting is left to the computer, ensuring consistent formatting across chordsheets and slides
* Efficient retrieval and organization of information, including publishing information, so users do not need to worry
about retrieving all of the information themselves

## Setup

If you just want to access the existing generated chordsheets, simply download directly from Github or clone the project.

To use this project to generate your own chordsheets, follow the below instructions:
1. Clone the project onto your local machine.

2. Install the `requests` and `python-gnupg` package through `pip`, `conda`, or another python package installer, e.g.
```
pip install requests python-gnupg
```

3. Install LaTeX, such as described [here](https://www.latex-project.org/get/). You will need to be able to run `pdflatex`
over command-line (through Python's `subprocess` module).

4. (Optional) If you want to generate PNG files for each slide, install ImageMagick as instructed [here](http://www.imagemagick.org/script/download.php).
Make sure that, by the end of installation, `convert` can be found in your `$PATH` variable (so that it can be run through Python's `subprocess` module).

5. (Optional) If you want to allow the tool to collect information about the song from the CCLI website, create a CCLI
account. To automatically save your CCLI information, save the username and password in the CONFIGURATION file, or enter
it in upon prompting during execution of the script.

6. Create a configuration file in your root project directory called `configuration.json`, and copy the following contents into it:
```
{
  "input_directory": "chordsheets_raw",
  "chordsheets_output_directory": "chordsheets_final",
  "slides_output_directory": "slides",
  "ccli_email_address": <email_address>
}
```
If you chose not to create a CCLI account, omit the last line.

7. (Optional) If you created a CCLI account, to create a GPG public/private key pair, run
```bash
python3 -m utils.create_key --user <email_address>
```
where `<email_address>` is the email address used for CCLI. Alternatively, you can also create the key with any email address (even a fake one) if you want.

8. (Optional) To encrypt your password for CCLI, run
```bash
python3 -m utils.encrypt --user <email_address>
```
Alternatively, if you have already put the email address in the configuration file and used the same one to generate your key,
you can run this wihtout the user input.

## Usage

To use this tool, refer to the below instructions. `$ROOT` will be used to refer to the root project directory.

1. Create the raw chordsheet in `$ROOT/chordsheets_raw`. Use `$ROOT/sample.txt` as a guide, or refer to any of the
pre-existing raw chordsheets as examples.

2. Run the script on the raw chordsheet by executing from command-line in the root project directory

```bash
python3 generate_music.py "<filename>.txt" <new_key>
```

Note that the script will look for your file in the `$ROOT/chordsheets_raw` directory. If your song title has whitespace
in it, you are recommended to surround the filename in quotes.

For example, to generate chordsheets and slides for "Lion and the Lamb" in B, one might run
```bash
python3 generate_music.py "Lion and the Lamb.txt" B
```

Generated chordsheets---both PDFs and tex files---are saved in `$ROOT/chordsheets_final`.

Generated slides, including the tex file, PDF, and PNG files---are saved in `$ROOT/slides`.

3. (Optional) If you need to make tweaks to the output files afterward, navigate to the appropriate directory, modify
the tex file, and recompile.

### Configuration

Should you desire to change the default directories in which the script looks for your raw chordsheets and outputs
generated chordsheets and slides, you can change the defaults in the `$ROOT/configuration.json` file.

If desired, the JSON format also supports a non-encrypted version of the password, with key `"ccli_password"` (in which
case you can skip steps 7 and 8). However, note that this is not recommended practice as it is insecure.

The old form of configuration file is also supported:
```
input_directory=chordsheets_raw
chordsheets_output_directory=chordsheets_final
slides_output_directory=slides
ccli_email_address=emailaddress@domain.com
ccli_password=yourpasswordhere
```
The file should be named as `CONFIGURATION`.

## Testing

This project has so far only been tested on the MacOS operating system with Python 3.6.x. Please report all bugs to
Austin Wang, but note that only limited support can be provided to non-UNIX-based systems.

## Feature Request

If you would like to contribute features, please contact Austin Wang.

Planned future feature improvements:
- [ ] Add support for MusicLine repeats
- [ ] Use HTML parser instead of Regex parser for CCLI requests
- [ ] Modify raw chordsheet to insert publication information for later offline chordsheet generation
- [ ] Add divider for paragraph breaks in chordsheet or slide breaks in slides
- [ ] Add support for beat numbers
- [ ] Add support for inline repeats
- [ ] Add support for guitar chords in sheet
- [ ] Better measure representation (better spacing?)
- [ ] More accurate internal representation of notes as whole tones and semitones
- [ ] Auto chord filling for similar sections
- [ ] Add support for converting Ultimate Guitar Tab style chordsheets into raw chordsheet format
- [ ] Detection of need for two columns (so lines don't have to be fit if only one column is used)
- [ ] Allow for comments in raw chordsheet (using //)
- [x] Encryption support for passwords