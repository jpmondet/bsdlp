#! /usr/bin/env python3

from argparse import ArgumentParser
from time import strftime


def handle_args():

    parser = ArgumentParser(
        prog="BSaviorLogParser", description="Parse Beat-savior log file to get important infos",
    )
    parser.add_argument(
        "-f",
        "--logfile",
        type=str,
        help="specify the logfile, default : _latest.log",
        default="_latest.log",
    )
    parser.add_argument(
        "-c",
        "--cleaned",
        type=bool,
        help="If this flag is set, we consider that files are already clean jsons",
    )
    parser.add_argument(
        "-tple",
        "--template",
        type=str,
        help="This flag goes with 'cleaned' if you want to indicate the name format of the files already cleaned",
    )
    parser.add_argument(
        "-d", "--directory", type=str, help="specify the directory in which to look for logs",
    )
    parser.add_argument(
        "-r",
        "--restrictmap",
        type=str,
        help="Restrict parsing to specific maps separated by double colons (name doesn't need to be exact. It will be greedy tho). For example 'map1' or 'map1::map2'.",
    )
    parser.add_argument(
        "-o",
        "--overall",
        type=int,
        help="Numbers of maps over ALL sessions (this option is not useful if you need to calculate only 1 session stats)",
        default=0,
    )
    parser.add_argument(
        "-g",
        "--graph",
        type=bool,
        help="Indicates that graph infos (as csv) must be generated (files in directory must have a name like {player}-{date}. For example: dude-20200606.log)",
    )
    parser.add_argument(
        "-w",
        "--show",
        type=bool,
        help="Indicates that graph must be built & shown (pairs with --graph option)",
    )
    parser.add_argument(
        "-dt",
        "--date",
        type=str,
        help="By default, date used is today. You can modify this with this option (must be formatted like : 20201230)",
        default=strftime("%Y%m%d"),
    )
    parser.add_argument(
        "-dp",
        "--deeptrackers",
        type=bool,
        help="With this option, deep trackers will be tacken in account & graphs per map/player will be showed",
    )
    parser.add_argument(
        "-dps",
        "--deeptrackerstoshow",
        type=str,
        help="By default, we try to show all we have. This option allows to select only some sub-deeptrackers (for example : 'preswing,postswing')",
        default="all",
    )
    parser.add_argument(
        "-ma",
        "--mapanalysis",
        type=str,
        help="If --deep-trackers option is used, it is possible to specify a map so that multiple runs of this map will be showed on the same graph (will only show the maps specified though)",
    )
    parser.add_argument(
        "-av",
        "--averagedMA",
        type=bool,
        help="If --mapanalysis option is used, it is possible to average the multiple runs into one",
    )
    parser.add_argument(
        "-nc",
        "--nocolor",
        type=bool,
        help="By default, output is colorize. You can disable it with this flag",
        default=False,
    )
    parser.add_argument(
        "-m",
        "--milestones",
        type=str,
        help="Allows to pass a milestones (as a json string) to check against",
    )
    parser.add_argument(
        "-t",
        "--top",
        type=bool,
        help="Shows only the best runs on each maps",
    )

    return parser.parse_args()