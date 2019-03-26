#!/usr/bin/env python3

"""
file: headers.py

Contains string versions of LaTeX file headers.
"""

# header for LaTeX chordsheets
CHORDSHEET_HEADER = \
    """\\documentclass[9pt]{extarticle}
    
    \\input{latex_templates/chordsheet}
    
    % SET THESE FOR THE SONG
    \\newcommand{\\name}{$song} % TITLE
    \\newcommand{\\ccli}{$ccli} % CCLI
    \\newcommand{\\composer}{$composer} % COMPOSER
    \\newcommand{\\bpm}{$bpm} % BEATS PER MINUTE
    \\newcommand{\\timesignature}{$signature} % TIME SIGNATURE
    \\newcommand{\\key}{$key} % KEY OF SONG
    \\newcommand{\\bibleverse}{$verse} % BIBLE VERSE REFERENCE
    \\newcommand{\\arranger}{$arranger} % ARRANGER
    
    \\fancyhead[L]{ \\\\ \\bpm\\ bpm, \\timesignature \\\\ \\key}
    \\fancyhead[C]{{\\Large \\bf{\\name}} \\\\ \\#\\ccli \\\\ \\bibleverse}
    \\fancyhead[R]{ \\\\ \\composer \\\\ \\arranger}
    """

# header for LaTeX beamer slides
SLIDES_HEADER = \
    """\\documentclass[xcolor=svgnames,table,aspectratio=169]{beamer}
    \\input{latex_templates/musicslides}
    
    \\newcommand{\\name}{$song}  % TITLE
    \\newcommand{\\composer}{$composer}  % COMPOSER
    \\renewcommand{\\year}{$year}  % YEAR OF PUBLISHING
    \\newcommand{\\publisher}{$publisher}  % PUBLISHER(S)
    \\newcommand{\\ccli}{$ccli}  % CCLI
    
    \\renewcommand{\\cite}{\\bottomleft{``\\name'' by \\composer\\\\\\textcopyright\\year\\ \\publisher\\\\CCLI License \\#\\ccli\\\\}}
    \\renewcommand{\\header}{\\topleft{\\name}}
    """