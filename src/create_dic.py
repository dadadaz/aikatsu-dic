"""
アイカツ辞書を作成するためのスクリプト。
Google日本語入力用，ATOK用に以下の辞書を作成することが可能。

・キャラクター名辞書
・楽曲名辞書

"""
import argparse
import os
from enum import Enum

MASTER_DIC_PATH = '../data/aikatsu_master_dic.tsv'


class DicVersion(Enum):
    """
    辞書の用途
    """
    GOOGLE = 'google'
    ATOK = 'atok'


class DicType(Enum):
    """
    辞書の種類
    """
    CHARACTER = 'character'
    MUSIC = 'music'


class Series(Enum):
    """
    アイカツのシリーズ
    """
    AIKATSU = 'aikatsu'
    AIKATSU_STARS = 'stars'
    AIKATSU_FRIENDS = 'friends'


class DicEntry(object):
    """
    アイカツ!辞書のマスターデータ内の1エントリ情報
    """

    def __init__(self, surface, normalized_surface, pos, yomi, series_set, dic_type):
        self.surface = surface
        self.normalized_surface = normalized_surface
        self.pos = pos
        self.yomi = yomi
        self.series_set = series_set
        self.dic_type = dic_type

    def __repr__(self):
        return ', '.join(['{}={}'.format(k, v) for k, v in self.__dict__.items()])


class MasterDic(object):
    """
    アイカツ辞書のマスターデータの情報を保持するクラス
    """

    def __init__(self, master_dic_path):
        self.__entries = self.read_master_dic(master_dic_path)

    @staticmethod
    def read_master_dic(dic_path):
        entries = []
        with open(dic_path, encoding='utf-8') as f:
            next(f)
            for line in f:
                line = line.rstrip()
                if not line:
                    continue
                cols = line.split('\t')
                if len(cols) != 6:
                    raise ValueError('Dic format is illegal.column size={},  input={}'.format(len(cols), line))
                series_set = set([Series(s) for s in cols[4].split(',')])
                dic_type = DicType(cols[5])
                entries.append(DicEntry(cols[0], cols[1], cols[2], cols[3], series_set, dic_type))
        return entries

    def extract(self, dic_type, series_set):
        """
        指定された条件に該当する辞書エントリを抽出する。
        :param dic_type: 辞書の種類
        :param series_set: 対象のシリーズset
        :return:
        """
        entries = []
        for entry in self.__entries:
            common_series = series_set & entry.series_set
            if entry.dic_type == dic_type and 0 < len(common_series):
                entries.append(entry)
        return entries


def reduce_entries_for_suggest_dic(entries):
    reduced_entries = []
    used_entries = set()
    for entry in entries:
        yomi_surface = (entry.yomi, entry.normalized_surface)
        if yomi_surface not in used_entries:
            used_entries.add(yomi_surface)
            reduced_entries.append(entry)
    print("prev entries: {}, reduced entries: {}".format(len(entries), len(reduced_entries)))
    return reduced_entries


def out_google_dic(out_dir, entries, dic_type):
    """
    google日本語入力用の辞書を作成する。
    ファイルのencodingはutf-8, 改行コードはCR/LF, タブ区切り。
    :param out_dir: 出力先ディレクトリ
    :param entries: 出力するエントリ
    :param dic_type: 辞書の種別
    """
    file_path = os.path.join(out_dir, 'google_dic_{}.txt'.format(dic_type.value))
    with open(file_path, 'w', encoding='utf-8') as f:
        for entry in reduce_entries_for_suggest_dic(entries):
            f.write('{}\t{}\t{}\n'.format(entry.yomi, entry.normalized_surface, entry.pos))


def out_atok_dic(out_dir, entries, dic_type):
    """
    ATOK用の辞書を作成する。
    ファイルのencodingはutf-16, 改行コードはCR/LF, タブ区切り。
    :param out_dir: 出力先ディレクトリ
    :param entries: 出力するエントリ
    :param dic_type: 辞書の種別
    """
    file_path = os.path.join(out_dir, 'atok_dic_{}.txt'.format(dic_type.value))

    with open(file_path, 'w', encoding='utf-16') as f:
        for entry in reduce_entries_for_suggest_dic(entries):
            f.write('{}\t{}\t{}\n'.format(entry.yomi, entry.normalized_surface, entry.pos))


def make_dir(out_dir):
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)


def create(out_dir, arg_version, arg_series):
    make_dir(out_dir)
    target_versions = set(DicVersion) if arg_version == 'all' else set(DicVersion(arg_version))
    target_series = set(Series) if arg_series == 'all' else set(Series[arg_series])
    master_dic = MasterDic(MASTER_DIC_PATH)

    for dic_type in DicType:
        entries = master_dic.extract(dic_type, target_series)
        for version in target_versions:
            print("Create {}'s {} dic.".format(version.value, dic_type.value))
            if version == DicVersion.GOOGLE:
                out_google_dic(out_dir, entries, dic_type)
            elif version == DicVersion.ATOK:
                out_atok_dic(out_dir, entries, dic_type)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
                                     """Aikatsu! dic creating tool.
                                     Containing dic types are `common`, `person`, `music`, `actor`, and `title`.
                                     """)
    # parser.add_argument('-m', '--mode', choices=['all', 'separate'], default='separate')
    parser.add_argument('-o', '--output_dir', default='../out')
    parser.add_argument('-v', '--version', choices=['all', 'google', 'atok'], default='all')
    parser.add_argument('-s', '--series', choices=['all', 'aikatsu', 'stars', 'friends'], default='all')
    args = parser.parse_args()
    create(args.output_dir, args.version, args.series)

