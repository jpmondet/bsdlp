""" This script computes a lot of stats from bsd logfiles.

usage: BSaviorLogParser [-h] [-f LOGFILE] [-d DIRECTORY] [-o OVERALL] [-g GRAPH] [-w SHOW]
                        [-dt DATE]

Parse Beat-savior log file to get important infos

optional arguments:
  -h, --help            show this help message and exit
  -f LOGFILE, --logfile LOGFILE
                        specify the logfile, default : _latest.log
  -d DIRECTORY, --directory DIRECTORY
                        specify the directory in which to look for logs
  -o OVERALL, --overall OVERALL
                        Numbers of maps over ALL sessions (this option is not useful if you need
                        to calculate only 1 session stats)
  -g GRAPH, --graph GRAPH
                        Indicates that graph infos (as csv) must be generated (files in directory
                        must have a name like {player}-{date}. For example: dude-20200606.log)
  -w SHOW, --show SHOW  Indicates that graph must be built & shown (pairs with --graph option)
  -dt DATE, --date DATE
                        By default, date used is today. You can modify this with this option (must
                        be formatted like : 20201230)
"""

#! /usr/bin/env python3

# line-too-long is disabled because of csv headers & some prints
# bad-continuation is disabled because is it handled by python-black
# pylint: disable=line-too-long, bad-continuation

from sys import exit as sexit # prevents redefining exit builtin
from os import access, R_OK, SEEK_SET, listdir, fsencode, fsdecode
from time import strftime, strptime
from argparse import ArgumentParser
import json

import requests
from colorama import Fore, Style #Back,
from matplotlib.pyplot import (
    get_cmap,
    style,
    plot,
    legend,
    title,
    xlabel,
    ylabel,
    grid,
    show,
    get_current_fig_manager,
    #savefig,
    #figure,
)


URLSS = "https://new.scoresaber.com/api/player/{}/full"
ID_PLAYERS = {}
MAPS_PLAYED = {}
CSVF_HEADER = "Rank,Player,Acc,Left Average,Left Before,Precision,Left After,Right Average,Right Before,Precision,Right After,Miss,Failed\n"
CSVF_HEADER_DISTANCE = "Rank,Player,Acc,Left Average,Left Before,Precision,Left After,Left Distance Saber,Left Distance Hand,Right Average,Right Before,Precision,Right After,Right Distance Saber,Right Distance Hand,Miss,Failed\n"
CSVF_HEADER_AVERAGE = "Rank,AvRank,Player,Acc,Left Average,Left Before,Precision,Left After,Right Average,Right Before,Precision,Right After,Miss,Nb Map Played,Nb Map Failed\n"
CSVF_HEADER_AVERAGE_DISTANCE = "Rank,AvRank,Player,Acc,Left Average,Left Before,Precision,Left After,Left Distance Saber,Left Distance Hand,Right Average,Right Before,Precision,Right After,Right Distance Saber,Right Distance Hand,Miss,Nb Map Played,Nb Map Failed\n"
MAPS_MISC_INFOS = {}
DATETIME = ""


def clean_logfile(logfile):

    cleaned_name = f"{logfile}_cleaned"

    cleaned_logfile = open(cleaned_name, "w")

    with open(logfile, "r") as logf:
        cleaned_logfile.write("[\n")
        for line in logf:
            line_cleaned = "".join(line.split("Data]")[1:])[1:]
            if "********" in line_cleaned:
                continue
            if "upload" in line_cleaned.lower():
                continue
            if "cheat in practice mode" in line_cleaned.lower():
                continue
            if "was a replay you cheater" in line_cleaned.lower():
                continue
            if line_cleaned.startswith("}"):
                line_cleaned = "},\n"
            if line_cleaned.endswith("}}\n"):
                line_cleaned += ",\n"
            cleaned_logfile.write(line_cleaned)

    cleaned_logfile.seek(cleaned_logfile.tell() - 2, SEEK_SET)
    cleaned_logfile.write("]")
    cleaned_logfile.close()

    return cleaned_name


def parse_logfile(cleaned_logfile):

    infos = []

    with open(cleaned_logfile, "r") as logf:
        try:
            infos = json.load(logf)
        except json.decoder.JSONDecodeError as jsonerr:
            print(jsonerr)
            sexit(1)

    return infos


def get_name_by_id(id_player):

    name_player = id_player

    if ID_PLAYERS.get(id_player):
        return ID_PLAYERS[id_player]["name"]

    try:
        req_infos_ssaber = requests.get(URLSS.format(id_player))
        req_infos_ssaber.raise_for_status()
        infos_ssaber = req_infos_ssaber.json()
        name_player = infos_ssaber["playerInfo"]["playerName"]
        ID_PLAYERS[id_player] = {}
        ID_PLAYERS[id_player]["name"] = name_player
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError):
        # Api is certainly dead or there is an issue with connection, we fallback to id...
        ID_PLAYERS[id_player] = {}
        ID_PLAYERS[id_player]["name"] = id_player

    return name_player


def retrieve_player_infos(info_map):

    id_player = info_map["playerID"]
    name = get_name_by_id(id_player)
    ID_PLAYERS[id_player]["av_score"] = info_map["averageCutScore"]
    ID_PLAYERS[id_player]["cumu_cut"] = info_map["cummulativeCutScoreWithoutMultiplier"]
    ID_PLAYERS[id_player]["tot_score"] = info_map["totalScore"]
    ID_PLAYERS[id_player]["bad_cuts"] = info_map["badCutsCount"]
    ID_PLAYERS[id_player]["good_cuts"] = info_map["goodCutsCount"]
    ID_PLAYERS[id_player]["miss_cuts"] = info_map["missedCutsCount"]
    ID_PLAYERS[id_player]["clear_lvl"] = info_map["clearedLevelsCount"]
    ID_PLAYERS[id_player]["failed_lvl"] = info_map["failedLevelsCount"]
    ID_PLAYERS[id_player]["played_lvl"] = info_map["playedLevelsCount"]
    ID_PLAYERS[id_player]["fc"] = info_map["fullComboCount"]
    ID_PLAYERS[id_player]["hand_dist"] = info_map["handDistanceTravelled"]
    ID_PLAYERS[id_player]["time_played"] = info_map["timePlayed"] / 3600

    print(
        f"{name} - time played: {ID_PLAYERS[id_player]['time_played']} - fc count : {ID_PLAYERS[id_player]['fc']}"
    )

def handle_notes_values(list_notes, map_name, player_name):
    """
    list of :
{
  "noteType": 0,
  "line": 3,
  "column": 0,
  "id": 0,
  "time": 1.4122833,
  "before": 70,
  "accuracy": 0,
  "after": 30,
  "timeDeviation": 0.04133582,
  "saberSpeed": 22.2724133,
  "cutDirDeviation": 0.164031982,
  "cutDistanceToCenter": 0.4768337
},

v2 :
{
  "noteType": 0,           <- left/right
  "noteDirection": 7,      <- rotation ?
                            -> Enum :
                                0 = up
                                1 = down
                                2 = left
                                3 = right
                                4 = upleft
                                5 = upright
                                6 = downleft
                                7 = downright
                                8 = Any
                                9 = None
  "index": 3,              <- placement (0 to 12 from bottom left to up right)
  "id": 0,                 <- noteOrder
  "time": 3.42305875,      <- time at which it appears
  "score": [               <- preswing/precision/postswing
    70,
    12,
    30
  ],
  "timeDeviation": 0.0356202126,  <- time at which it was hit
  "cutPoint": [                   <- x,y,z, where is 0 ?
    0.960040569,
    0.8226648,
    1.36074
  ],
  "saberDir": [
    0.06795776,
    -0.224361658,
    0.06975007
  ]
},

v3:

{"noteType":0,"noteDirection":1,"index":1,"id":31,"time":3.38983059,"cutType":0,"multiplier":1,"score":[70,11,30],"timeDeviation":0.0441668034,"cutPoint":[0.226540029,0.813864648,1.58848751],"saberDir":[-0.00422650576,-0.298254728,0.005454302]}

    cutType -> enum (0 = cut, 1 = miss, 2 = badcut)
    multiplier -> allows to see when a wall is hit

    """
    sorted_notes = sorted(
        list_notes, key=lambda kv: kv["id"]
    )
    x_note_time = []
    y_acc = []
    y_preswing = []
    y_precision = []
    y_postswing = []
    y_time_deviation = []
    for note in sorted_notes:
        x_note_time.append(note["time"])
        acc_note = int(note["score"][0]) + int(note["score"][1]) + int(note["score"][2])
        y_acc.append(acc_note)
        y_preswing.append(note["score"][0])
        y_precision.append(note["score"][1])
        y_postswing.append(note["score"][2])
        y_time_deviation.append(float(note["timeDeviation"]) * 1000)  # in milliseconds

    all_y = {
            "Acc": y_acc,
            "Preswing": y_preswing,
            "TimeDeviation": y_time_deviation,
            "Precision": y_precision,
            "Postswing": y_postswing,
    }

    style.use("dark_background")
    palette = get_cmap("Set1")
    color = 0
    for y_name, y_vals in all_y.items():
        linewidth = 1 if y_name == "TimeDeviation" else 2
        plot(
            x_note_time,
            y_vals,
            marker="",
            color=palette(color),
            linewidth=linewidth,
            alpha=0.9,
            label=y_name,
        )
        color += 1

    legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.15),
        ncol=5,
        fancybox=True,
        shadow=True,
    )
    title(f"|{player_name}| ({map_name})", loc="left", fontsize=14, fontweight=4, color="White")
    xlabel("Time")
    ylabel("Points & millisecs")
    grid()
    mng = get_current_fig_manager()
    mng.resize(*mng.window.maxsize())
    show()


def retrieve_relevant_infos(infos):

    map_dict = {}  # stores player infos per map
    averages_dict = {}  # stores averages per player

    for info_map in infos:

        if info_map.get("saberAColor"):
            retrieve_player_infos(info_map)
            continue
        # Retrieving all relevant infos into variables
        name = get_name_by_id(info_map["playerID"])
        score = info_map["trackers"]["scoreTracker"]["score"]
        pauses = info_map["trackers"]["winTracker"]["nbOfPause"]
        map_passed = info_map["trackers"]["winTracker"]["won"]
        failed_time = info_map["trackers"]["winTracker"]["endTime"]
        misses = info_map["trackers"]["hitTracker"]["miss"]
        acc = float(info_map["trackers"]["scoreTracker"]["modifiedRatio"]) * 100
        acc_left = float(info_map["trackers"]["accuracyTracker"]["accLeft"])
        acc_right = float(info_map["trackers"]["accuracyTracker"]["accRight"])
        try:
            left_av_tuple = (
                float(info_map["trackers"]["accuracyTracker"]["leftAverageCut"][0]),
                float(info_map["trackers"]["accuracyTracker"]["leftAverageCut"][1]),
                float(info_map["trackers"]["accuracyTracker"]["leftAverageCut"][2]),
            )
            right_av_tuple = (
                float(info_map["trackers"]["accuracyTracker"]["rightAverageCut"][0]),
                float(info_map["trackers"]["accuracyTracker"]["rightAverageCut"][1]),
                float(info_map["trackers"]["accuracyTracker"]["rightAverageCut"][2]),
            )
        except KeyError:
            left_av_tuple = (0.0, 0.0, 0.0)
            right_av_tuple = (0.0, 0.0, 0.0)
        if "," in info_map["songMapper"]:
            info_map["songMapper"] = info_map["songMapper"].split(",")[0]
        map_name = f"{info_map['songName']} {info_map['songArtist']} {info_map['songDifficulty']} by {info_map['songMapper']}"

        if info_map.get("deepTrackers"):
            handle_notes_values(info_map["deepTrackers"]["noteTracker"]["notes"], map_name, name)

        try:
            # If BSD version supports distanceTracker
            distance_rsaber = float(
                info_map["trackers"]["distanceTracker"]["rightSaber"]
            )
            distance_lsaber = float(
                info_map["trackers"]["distanceTracker"]["leftSaber"]
            )
            distance_lhand = float(info_map["trackers"]["distanceTracker"]["leftHand"])
            distance_rhand = float(info_map["trackers"]["distanceTracker"]["rightHand"])
            nb_with_distance = 1
        except KeyError:
            # distanceTracker not support
            distance_rsaber = 0.0
            distance_lsaber = 0.0
            distance_lhand = 0.0
            distance_rhand = 0.0
            nb_with_distance = 0

        if MAPS_PLAYED.get(map_name):
            if name in MAPS_PLAYED[map_name]["players"]:
                MAPS_PLAYED[map_name]["count"] += 1
            else:
                MAPS_PLAYED[map_name]["players"].append(name)
        else:
            MAPS_PLAYED[map_name] = {"count": 1, "players": [name]}

        # Preparing values for map_dict and storing them
        acc_format = "{:.2f}".format(acc)
        acc_left_format = "{:.2f}".format(acc_left)
        acc_right_format = "{:.2f}".format(acc_right)
        left_av_format = "{:05.2f}, {:05.2f}, {:05.2f}".format(
            left_av_tuple[0], left_av_tuple[1], left_av_tuple[2]
        )
        right_av_format = "{:05.2f}, {:05.2f}, {:05.2f}".format(
            right_av_tuple[0], right_av_tuple[1], right_av_tuple[2]
        )
        distance_rsaber_format = (
            "{:.2f}".format(distance_rsaber) if distance_rsaber else ""
        )
        distance_lsaber_format = (
            "{:.2f}".format(distance_lsaber) if distance_lsaber else ""
        )
        distance_lhand_format = (
            "{:.2f}".format(distance_rhand) if distance_rhand else ""
        )
        distance_rhand_format = (
            "{:.2f}".format(distance_lhand) if distance_lhand else ""
        )
        player_infos = {
            "id": name,
            "score": score,
            "acc": acc_format,
            "accLeft": acc_left_format,
            "accRight": acc_right_format,
            "leftAv": left_av_format,
            "rightAv": right_av_format,
            "pause": pauses,
            "miss": misses,
            "map_passed": map_passed,
            "failed_time": failed_time,
            "distance_rsaber": distance_rsaber_format,
            "distance_lsaber": distance_lsaber_format,
            "distance_rhand": distance_rhand_format,
            "distance_lhand": distance_lhand_format,
        }
        try:
            map_dict[map_name].append(player_infos)
        except KeyError:
            map_dict[map_name] = [player_infos]

        # Preparing value for averages_dict and storing it
        try:
            if map_passed:
                averages_dict[name]["list_map_passed"].append(map_name)
                averages_dict[name]["nb_map_passed"] += 1
            else:
                averages_dict[name]["list_map_failed"].append(map_name)
                averages_dict[name]["nb_map_failed"] += 1
            averages_dict[name]["score"] += score
            averages_dict[name]["acc"] += acc
            averages_dict[name]["accLeft"] += acc_left
            averages_dict[name]["accRight"] += acc_right
            prev_left_av_tuple = averages_dict[name]["leftAv"]
            prev_right_av_tuple = averages_dict[name]["rightAv"]
            averages_dict[name]["leftAv"] = tuple(
                map(sum, zip(prev_left_av_tuple, left_av_tuple))
            )
            averages_dict[name]["rightAv"] = tuple(
                map(sum, zip(prev_right_av_tuple, right_av_tuple))
            )
            averages_dict[name]["pause"] += pauses
            averages_dict[name]["miss"] += misses
            averages_dict[name]["nb_map_played"] += 1
            if distance_lhand:
                averages_dict[name]["distance_rsaber"] += distance_rsaber
                averages_dict[name]["distance_lsaber"] += distance_lsaber
                averages_dict[name]["distance_rhand"] += distance_rhand
                averages_dict[name]["distance_lhand"] += distance_lhand
                averages_dict[name]["nb_with_distance"] += 1
        except KeyError:
            if map_passed:
                list_map_passed = [map_name]
                list_map_failed = []
                nb_map_passed = 1
                nb_map_failed = 0
            else:
                list_map_passed = []
                list_map_failed = [map_name]
                nb_map_passed = 0
                nb_map_failed = 1
            averages_infos = {
                "id": name,
                "score": score,
                "acc": acc,
                "accLeft": acc_left,
                "accRight": acc_right,
                "leftAv": left_av_tuple,
                "rightAv": right_av_tuple,
                "pause": pauses,
                "miss": misses,
                "nb_map_passed": nb_map_passed,
                "list_map_passed": list_map_passed,
                "list_map_failed": list_map_failed,
                "nb_map_failed": nb_map_failed,
                "nb_map_played": 1,
                "distance_rsaber": distance_rsaber,
                "distance_lsaber": distance_lsaber,
                "distance_rhand": distance_rhand,
                "distance_lhand": distance_lhand,
                "nb_with_distance": nb_with_distance,
            }
            averages_dict[name] = averages_infos
    return map_dict, averages_dict


def get_ranking_per_map(maps_dict):
    player_ranking_dict = {}
    for map_name in maps_dict.keys():
        sorted_pinfos = sorted(
            maps_dict[map_name], key=lambda kv: kv["score"], reverse=True
        )
        for rank, pinfos in enumerate(sorted_pinfos):
            try:
                if player_ranking_dict[pinfos["id"]].get(map_name):
                    player_ranking_dict[pinfos["id"]][map_name].append(rank + 1)
                else:
                    player_ranking_dict[pinfos["id"]][map_name] = [rank + 1]
            except KeyError:
                player_ranking_dict[pinfos["id"]] = {map_name: [rank + 1]}
    return player_ranking_dict


def show_relevant_infos(maps_dict):

    infos = maps_dict

    for map_name in infos.keys():
        print(f"{Style.BRIGHT}{map_name}{Style.RESET_ALL}")
        sorted_pinfos = sorted(
            infos[map_name], key=lambda kv: kv["score"], reverse=True
        )
        for rank, pinfos in enumerate(sorted_pinfos):
            # if pinfos['distance_rsaber']:
            print(
                f"     {rank + 1} -  {pinfos['id']:28} with {pinfos['acc']:5}   (left: {pinfos['accLeft']:6} [{pinfos['leftAv']:>18}]{Style.DIM}{Fore.BLUE}[{pinfos['distance_lsaber']:>8},{pinfos['distance_lhand']:>8}]{Style.RESET_ALL}, right: {pinfos['accRight']:6} [{pinfos['rightAv']:>18}]{Style.DIM}{Fore.BLUE}[{pinfos['distance_rsaber']:>8},{pinfos['distance_rhand']:>8}]{Style.RESET_ALL}, {pinfos['miss']} miss)"
            )
            # else:
            #    print(f"     {rank + 1} -  {pinfos['id']:20} with {pinfos['acc']:5}   (left: {pinfos['accLeft']:6} [{pinfos['leftAv']:>18}], right: {pinfos['accRight']:6} [{pinfos['rightAv']:>18}], {pinfos['miss']} miss)")
            if int(pinfos["pause"]) > 0:
                print(
                    f"                {Fore.RED}/!\\ Paused {pinfos['pause']} times !!!{Style.RESET_ALL}"
                )
            if not pinfos["map_passed"]:
                print(
                    f"                {Fore.RED}/!\\ Map failed at {pinfos['failed_time']:.2f} seconds{Style.RESET_ALL}"
                )
        print()


def get_average_ranking(player_ranking_dict, nb_map_played):
    #played_all = True
    rank_sum = 0
    for _, ranks in player_ranking_dict.items():
        rank_sum += sum(ranks)
    return rank_sum / nb_map_played


def show_averages(averages_dict, maps_dict, overall=0):
    players_ranking_dict = get_ranking_per_map(maps_dict)
    infos = averages_dict

    sorted_pinfos = sorted(infos.items(), key=lambda kv: kv[1]["score"], reverse=True)

    nb_players = len(ID_PLAYERS.keys())
    nb_map_session = 0
    if overall:
        nb_map_session = overall
    else:
        nb_map_session = sum([value["count"] for value in MAPS_PLAYED.values()])

    line_in_csv = []

    print(
        f"{Style.BRIGHT}### AVERAGES OF THE WHOLE SESSION (sorted by total score on all maps) ###{Style.RESET_ALL}"
    )
    for rank, averages in enumerate(sorted_pinfos):
        name, pinfos = averages

        av_rank = get_average_ranking(
            players_ranking_dict[name], pinfos["nb_map_played"]
        )
        #played_all = True if pinfos["nb_map_played"] == nb_map_session else False
        played_all = pinfos["nb_map_played"] == nb_map_session

        av_acc = pinfos["acc"] / pinfos["nb_map_played"]
        av_acc_left = pinfos["accLeft"] / pinfos["nb_map_played"]
        av_left_ac_before = pinfos["leftAv"][0] / pinfos["nb_map_played"]
        av_left_ac_precision = pinfos["leftAv"][1] / pinfos["nb_map_played"]
        av_left_ac_after = pinfos["rightAv"][2] / pinfos["nb_map_played"]
        av_right_ac_before = pinfos["rightAv"][0] / pinfos["nb_map_played"]
        av_right_ac_precision = pinfos["rightAv"][1] / pinfos["nb_map_played"]
        av_right_ac_after = pinfos["leftAv"][2] / pinfos["nb_map_played"]
        av_acc_right = pinfos["accRight"] / pinfos["nb_map_played"]
        av_misses = pinfos["miss"] / pinfos["nb_map_played"]
        av_pauses = pinfos["pause"] #/ pinfos["nb_map_played"]
        map_passed = ", ".join(pinfos["list_map_passed"])
        map_failed = ", ".join(pinfos["list_map_failed"])
        nb_map_failed = pinfos["nb_map_failed"]
        nb_map_passed = pinfos["nb_map_passed"]
        if pinfos["nb_with_distance"]:
            distance_rsaber = pinfos["distance_rsaber"] / pinfos["nb_with_distance"]
            distance_lsaber = pinfos["distance_lsaber"] / pinfos["nb_with_distance"]
            distance_rhand = pinfos["distance_rhand"] / pinfos["nb_with_distance"]
            distance_lhand = pinfos["distance_lhand"] / pinfos["nb_with_distance"]
        else:
            distance_rsaber = 0
            distance_lsaber = 0
            distance_rhand = 0
            distance_lhand = 0

        rank_format = "{:.2f}".format(av_rank)
        acc_format = "{:.2f}".format(av_acc)
        acc_left_format = "{:.2f}".format(av_acc_left)
        acc_right_format = "{:.2f}".format(av_acc_right)
        left_av_format = "{:05.2f}, {:05.2f}, {:05.2f}".format(
            av_left_ac_before, av_left_ac_precision, av_left_ac_after
        )
        right_av_format = "{:05.2f}, {:05.2f}, {:05.2f}".format(
            av_right_ac_before, av_right_ac_precision, av_right_ac_after
        )
        distance_rsaber_format = (
            "{:.2f}".format(distance_rsaber) if distance_rsaber else ""
        )
        distance_lsaber_format = (
            "{:.2f}".format(distance_lsaber) if distance_lsaber else ""
        )
        distance_rhand_format = (
            "{:.2f}".format(distance_rhand) if distance_rhand else ""
        )
        distance_lhand_format = (
            "{:.2f}".format(distance_lhand) if distance_lhand else ""
        )
        # if distance_rhand:
        print(
            f"{rank+1} - {Style.DIM}(AvRank:{rank_format}){Style.RESET_ALL} - {Style.BRIGHT}{name:28}{Style.RESET_ALL} with {acc_format:5}   (left: {acc_left_format:6} [{left_av_format:>18}]{Style.DIM}{Fore.BLUE}[{distance_lsaber_format:>8},{distance_lhand_format:>8}]{Style.RESET_ALL}, right: {acc_right_format:6} [{right_av_format:>18}]{Style.DIM}{Fore.BLUE}[{distance_rsaber_format:>8},{distance_rhand_format:>8}]{Style.RESET_ALL}, {av_misses:.2f} miss)"
        )
        # else:
        #    print(f"{rank+1} - {Style.DIM}(AvRank:{rank_format}){Style.RESET_ALL} - {Style.BRIGHT}{name:20}{Style.RESET_ALL} with {acc_format:5}   (left: {acc_left_format:6} [{left_av_format:>18}], right: {acc_right_format:6} [{right_av_format:>18}], {av_misses:.2f} miss)")
        if not played_all:
            print(
                f"{Fore.RED}                             /!\\ Can be tricky to analyze since this player {Style.BRIGHT}didn't play all maps ({pinfos['nb_map_played']}/{nb_map_session}){Style.RESET_ALL}"
            )
        if nb_map_failed > 0:
            print(
                f"{Fore.YELLOW}                             /!\\ Can be tricky to analyze since this player {Style.BRIGHT}failed some maps ({nb_map_failed}/{nb_map_session}){Style.RESET_ALL}"
            )
        if int(pinfos["pause"]) > 0:
            print(
                f"{Fore.RED}                             /!\\ Paused {pinfos['pause']} times !{Style.RESET_ALL}"
            )
        # if distance_rhand:
        line_in_csv.append(
            (
                distance_lsaber_format,
                distance_rsaber_format,
                distance_lhand_format,
                distance_rhand_format,
                rank + 1,
                rank_format,
                name,
                acc_format,
                acc_left_format,
                left_av_format,
                acc_right_format,
                right_av_format,
                av_misses,
                pinfos["nb_map_played"],
                nb_map_failed,
                nb_map_session,
            )
        )
        # else:
        #    line_in_csv.append((rank+1, rank_format, name, acc_format, acc_left_format, left_av_format, acc_right_format, right_av_format, av_misses, pinfos['nb_map_played'], nb_map_failed, nb_map_session))
        rank += 1
    print()
    averages_as_csv(line_in_csv)


def relevant_infos_as_csv(maps_dict):

    infos = maps_dict

    # with open(f"infos-{strftime('%Y%m%d')}.csv",'w') as csvf:
    with open(f"infos-{DATETIME}.csv", "w") as csvf:
        csvf.write("Maps played\n")
        for map_name in infos.keys():
            csvf.write(f"{map_name}\n")
        csvf.write("\nDetails per map")
        for map_name in infos.keys():
            csvf.write(f"\n{map_name}\n")
            # if infos[map_name][0]['distance_rhand']:
            csvf.write(CSVF_HEADER_DISTANCE)
            # else:
            #    csvf.write(CSVF_HEADER)
            sorted_pinfos = sorted(
                infos[map_name], key=lambda kv: kv["score"], reverse=True
            )
            for rank, pinfos in enumerate(sorted_pinfos):
                failed = (
                    f"Failed at {pinfos['failed_time']:.2f}"
                    if not pinfos["map_passed"]
                    else ""
                )
                # if pinfos['distance_rhand']:
                csvf.write(
                    f"{rank + 1},{pinfos['id']},{pinfos['acc']},{pinfos['accLeft']},{pinfos['leftAv']},{pinfos['distance_lsaber']},{pinfos['distance_lhand']},{pinfos['accRight']},{pinfos['rightAv']},{pinfos['distance_rsaber']},{pinfos['distance_rhand']},{pinfos['miss']},{failed}\n"
                )
                # else:
                #    csvf.write(f"{rank + 1},{pinfos['id']},{pinfos['acc']},{pinfos['accLeft']},{pinfos['leftAv']},{pinfos['accRight']},{pinfos['rightAv']},{pinfos['miss']},{failed}\n")


def averages_as_csv(lines):
    # with open(f"av_infos-{strftime('%Y%m%d')}.csv",'w') as csvf:
    with open(f"av_infos-{DATETIME}.csv", "w") as csvf:
        # csvf.write(f"{{strftime('%Y%m%d')}\n")
        if DATETIME == "overall":
            csvf.write(f"{DATETIME}\n")
            csvf.write("Nb Maps,Type\n")
            csvf.write(f"{lines[0][-1]},\n")
        else:
            csvf.write(f"{strftime('%d/%m/%Y', strptime(DATETIME,'%Y%m%d'))}\n")
            csvf.write("Nb Maps,Type\n")
            csvf.write(f"{lines[0][-1]},\n\n")
        # if len(lines[0]) > 12:
        #    csvf.write(CSVF_HEADER_AVERAGE)
        # else:
        csvf.write(CSVF_HEADER_AVERAGE_DISTANCE)
        for line in lines:
            # if len(line) > 12:
            (
                dls,
                dlh,
                drs,
                drh,
                rank,
                rank_format,
                name,
                acc_format,
                acc_left_format,
                left_av_format,
                acc_right_format,
                right_av_format,
                av_misses,
                nb_map_played,
                nb_map_failed,
                nb_map_session,
            ) = line
            csvf.write(
                f"{rank},{rank_format},{name},{acc_format},{acc_left_format},{left_av_format},{dls},{dlh},{acc_right_format},{right_av_format},{drs},{drh},{av_misses:.2f},{nb_map_played},{nb_map_failed}\n"
            )
            # else:
            #    rank, rank_format, name, acc_format, acc_left_format, left_av_format, acc_right_format, right_av_format, av_misses, nb_map_played, nb_map_failed, nb_map_session = line
            #    csvf.write(f"{rank},{rank_format},{name},{acc_format},{acc_left_format},{left_av_format},{acc_right_format},{right_av_format},{av_misses:.2f},{nb_map_played},{nb_map_failed}\n")


def get_files_in_dir(directory_in_str):

    list_files = []
    directory = fsencode(directory_in_str)
    for logfile in listdir(directory):
        list_files.append(f"{directory_in_str}/{fsdecode(logfile)}")

    return list_files


def merge_files(cleaned_list):
    # merged_file = f"cleaned-{strftime('%Y%m%d')}.log"
    merged_file = f"cleaned-{DATETIME}.log"
    with open(merged_file, "w") as outfile:
        for fname in cleaned_list:
            with open(fname) as infile:
                outfile.write(infile.read())

    return merged_file


def load_diff_maps():
    # maps_train_file = "train.json"
    bswc_diff_maps_file = "maps_diffs.csv"
    type_maps_file = "maps_types.csv"

    # Bsaver considers me as a bot... Nice !
    # with open(maps_train_file, "r") as mtf:
    #    maps_train = json.load(mtf)
    # for map_train in maps_train['songs']:
    # maps_bsaver = requests.get(f"https://beatsaver.com/api/maps/by-hash/{hash_id}").json()
    # print(maps_bsaver["metadata"]["songName"], maps_bsaver["metadata"]["songAuthorName"], "by", maps_bsaver["metadata"]["songName"])

    with open(type_maps_file, "r") as tmf:
        for line in tmf:
            splitted = line.split(",")
            time_map = splitted[-1][:-1]
            type_map = splitted[-2]
            diff_map = splitted[-3]
            mapper_map = splitted[-4]
            author_map = splitted[-5]
            name_map = splitted[0]
            if len(splitted[0:-5]) > 1:
                name_map = ",".join(splitted[0:-5])
                # name_map = name_map[:-1]
            name_map_full = (
                f"{name_map} {author_map} {diff_map} by {mapper_map}".lower()
            )
            # print(name_map_full)
            MAPS_MISC_INFOS[name_map_full.strip()] = {
                "time": time_map,
                "type": type_map,
                "diff": diff_map,
                "mapper": mapper_map,
                "author": author_map,
            }

    # print(json.dumps(MAPS_MISC_INFOS, indent=2))

    with open(bswc_diff_maps_file, "r") as dmf:
        for line in dmf:
            splitted = line.split(",")
            diff = splitted[0]
            name = ",".join(splitted[1:])
            name = name[:-1].lower()
            if name:
                MAPS_MISC_INFOS[name.strip()]["bswc_type"] = diff


def classify_reference_maps_per_type(maps_by_name):

    type_maps = {}

    for name, infos in maps_by_name.items():
        try:
            type_maps[infos["type"]].append(name)
        except KeyError:
            type_maps[infos["type"]] = [name]
    return type_maps


def classify_played_maps_per_type_and_date(maps_dict, date, played_type_maps):

    for map_name, infos in maps_dict.items():
        try:
            map_misc_infos = MAPS_MISC_INFOS[map_name.lower()]
        except KeyError:
            print(f"Map not referenced : {map_name.lower()}")
            continue
        try:
            played_type_maps[map_misc_infos["type"]][date].append({map_name: infos})
        except KeyError:
            played_type_maps[map_misc_infos["type"]][date] = [{map_name: infos}]

    # print(json.dumps(played_type_maps, indent=2))

    return played_type_maps


def update_averages_for_map(infos_players, players_averages):

    for player in infos_players:
        try:
            players_averages[player["id"]]["acc"] += float(player["acc"])
            players_averages[player["id"]]["nb_map_played"] += 1
        except KeyError:
            players_averages[player["id"]] = {
                "acc": float(player["acc"]),
                "nb_map_played": 1,
            }

    return players_averages


def get_averages_on_date(maps, date, players_averages):
    for map_played in maps:
        _, infos_players = map_played.popitem()
        players_averages = update_averages_for_map(infos_players, players_averages)

    for name_p, stats in players_averages.items():
        players_averages[name_p][date] = {
            "av_acc": float(stats["acc"]) / float(stats["nb_map_played"])
        }

    return players_averages


def get_x_y_from_maps_per_type_and_date(maps_per_type_and_date):

    xy_per_type = {}
    for type_maps in maps_per_type_and_date.keys():
        dates_x_axis = sorted(maps_per_type_and_date[type_maps].keys())
        players_averages = {}
        #nb_players = 0
        for date in dates_x_axis:
            players_averages = get_averages_on_date(
                maps_per_type_and_date[type_maps][date], date, players_averages
            )

        av_for_players_y_axis = {}

        for name_p, stats in players_averages.items():
            averages_y_for_player = []
            for date in dates_x_axis:
                try:
                    averages_y_for_player.append(stats[date]["av_acc"])
                except KeyError:
                    averages_y_for_player.append(None)
            av_for_players_y_axis[name_p] = averages_y_for_player
        xy_per_type[type_maps] = (dates_x_axis, av_for_players_y_axis)

    return xy_per_type


def plot_graph(xy_per_type):

    # styles available : ['Solarize_Light2', '_classic_test_patch', 'bmh', 'classic', 'dark_background', 'fast', 'fivethirtyeight', 'ggplot', 'grayscale', 'seaborn', 'seaborn-bright', 'seaborn-colorblind', 'seaborn-dark', 'seaborn-dark-palette', 'seaborn-darkgrid', 'seaborn-deep', 'seaborn-muted', 'seaborn-notebook', 'seaborn-paper', 'seaborn-pastel', 'seaborn-poster', 'seaborn-talk', 'seaborn-ticks', 'seaborn-white', 'seaborn-whitegrid', 'tableau-colorblind10']
    style.use("dark_background")
    palette = get_cmap("Set1")

    for type_maps in xy_per_type.keys():
        print(f"Graph for {type_maps}\n")
        x_axis, all_y = xy_per_type[type_maps]

        for palette_color, player in enumerate(all_y.keys()):
            # fig = figure(palette_color)
            plot(
                x_axis,
                all_y[player],
                marker="",
                color=palette(palette_color),
                linewidth=2,
                alpha=0.9,
                label=player,
            )
        legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.15),
            ncol=4,
            fancybox=True,
            shadow=True,
        )
        title(type_maps, loc="left", fontsize=24, fontweight=4, color="orange")
        xlabel("Date")
        ylabel("Score")
        grid()
        mng = get_current_fig_manager()
        mng.resize(*mng.window.maxsize())
        # mng.window.state('zoomed')
        # mng.frame.Maximize(True)
        show()
        # savefig(f'{type_maps}.png', orientation='landscape', papertype='a0', bbox_inches='tight')


def graphs_averages_per_type_and_date_as_csv(
    maps_per_type_and_date, plot_and_show=False
):

    xy_per_type = get_x_y_from_maps_per_type_and_date(maps_per_type_and_date)

    with open("graphs_averages_per_type_and_date.csv", "w") as gaptadf:

        #for type_maps in xy_per_type.keys():
        for type_maps in xy_per_type:
            dates, players_averages = xy_per_type[type_maps]
            gaptadf.write(f"{type_maps}\n")
            gaptadf.write(f"Players,{','.join(dates)}\n")
            nb_players = len(players_averages.keys())
            for player, averages in players_averages.items():
                gaptadf.write(f"{player},")
                for average in averages:
                    if average:
                        gaptadf.write(f"{average:.2f},")
                    else:
                        gaptadf.write(",")
                gaptadf.write("\n")
            gaptadf.write("\n" * (11 - nb_players))

    if plot_and_show:
        plot_graph(xy_per_type)


def classify_files_of_directory_by_date(directory):
    list_files = get_files_in_dir(directory)
    # Sort files by date:
    # list_files_sorted = sorted(list_files, key=lambda f: f.split('-')[1][:-4])
    files_by_date = {}
    for logfile in list_files:
        print(logfile)
        date = logfile.split("_")[1][:-4]
        date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
        print(date)
        try:
            files_by_date[date].append(logfile)
        except KeyError:
            files_by_date[date] = [logfile]
    return files_by_date


def main():
    parser = ArgumentParser(
        prog="BSaviorLogParser",
        description="Parse Beat-savior log file to get important infos",
    )
    parser.add_argument(
        "-f",
        "--logfile",
        type=str,
        help="specify the logfile, default : _latest.log",
        default="_latest.log",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        help="specify the directory in which to look for logs",
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
    global DATETIME # pylint: disable=global-statement

    args = parser.parse_args()

    logfile = args.logfile

    if args.overall > 0:
        DATETIME = "overall"
    else:
        try:
            strptime(args.date, "%Y%m%d")
            DATETIME = args.date
        except ValueError:
            print("Date format not ok, defaulting to today")
            DATETIME = strftime("%Y%m%d")

    print(DATETIME)

    if args.directory:
        list_files = get_files_in_dir(args.directory)
        logfile = merge_files(list_files)

    else:
        if not access(args.logfile, R_OK):
            print("Please provide a correct file path")
            sexit(1)

    cleaned_logfile = clean_logfile(logfile)
    infos = parse_logfile(cleaned_logfile)

    map_dict, averages_dict = retrieve_relevant_infos(infos)
    show_relevant_infos(map_dict)
    relevant_infos_as_csv(map_dict)

    # print(json.dumps(map_dict, indent=2))
    # print(json.dumps(averages_dict, indent=2))
    # show_relevant_infos(averages_dict)
    show_averages(averages_dict, map_dict, args.overall)

    if args.graph and args.directory:
        # Prepare maps infos with difficulty and stuff
        load_diff_maps()
        global_type_maps = classify_reference_maps_per_type(MAPS_MISC_INFOS)
        types = global_type_maps.keys()
        maps_per_type_and_date = {}
        for type_maps in types:
            maps_per_type_and_date[type_maps] = {}

        # Try to cut the problem into pieces (by days)
        files_by_date = classify_files_of_directory_by_date(args.directory)
        for date, files in files_by_date.items():
            logfile = merge_files(files)
            cleaned_logfile = clean_logfile(logfile)
            infos = parse_logfile(cleaned_logfile)
            map_dict, averages_dict = retrieve_relevant_infos(infos)

            maps_per_type_and_date = classify_played_maps_per_type_and_date(
                map_dict, date, maps_per_type_and_date
            )
        graphs_averages_per_type_and_date_as_csv(maps_per_type_and_date, args.show)


if __name__ == "__main__":
    main()
