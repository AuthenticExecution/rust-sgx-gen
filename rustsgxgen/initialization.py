import sys
import argparse
import logging
import colorlog
import os
import base64

from . import conf

def _set_parser():
    parser = argparse.ArgumentParser(description='Authentic Execution SGX')
    parser.add_argument('-l', '--loglevel', nargs='?', default=conf.DEFAULT_LOG_LEVEL, type=__log_level)
    parser.add_argument('-i', '--input', required=True, type=__input_dir, help='Input folder of the software module')
    parser.add_argument('-o', '--output', required=True, type=__output_dir, help='Output folder of the software module')
    parser.add_argument('-m', '--moduleid', required=True, type=__int16bits, help='16-bit Module ID')
    parser.add_argument('-k', '--key', required=False, action='store_const', help='128-bit module\'s symmetric key', const=__generate_key(16))
    parser.add_argument('-e', '--emport', required=True, type=__int16bits, help='EM TCP port')
    parser.add_argument('-r', '--runner', type=__runner, required=False, default=conf.DEFAULT_RUNNER, help='Runner name')
    parser.add_argument('-s', '--spkey', required=False, type=__sp_key, help='Path to ra_sp public key')
    parser.add_argument('-p', '--print', #type=module_info, # uncomment if you want to check if file already exists
    help='Output module\'s info path')
    return parser


def _set_logging(loglevel):
    log = logging.getLogger()

    format_str = '%(asctime)s.%(msecs)03d - %(levelname)-8s: %(message)s'
    date_format = '%H:%M:%S' #'%Y-%m-%d %H:%M:%S'
    if os.isatty(2):
        cformat = '%(log_color)s' + format_str
        colors = {'DEBUG': 'reset',
                  'INFO': 'bold_green',
                  'WARNING': 'bold_yellow',
                  'ERROR': 'bold_red',
                  'CRITICAL': 'bold_red'}
        formatter = colorlog.ColoredFormatter(cformat, date_format,
                                              log_colors=colors)
    else:
        formatter = logging.Formatter(format_str, date_format)

    log.setLevel(loglevel)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)


def __int16bits(arg):
    arg = int(arg)
    if arg < 0 or arg > 65535:
        raise argparse.ArgumentTypeError("Invalid Module ID: must be between 0 and 65535")

    return arg


def __str16bytes(arg):
    if len(arg) > 16:
        raise argparse.ArgumentTypeError("Invalid key: must be a 16-bytes string")

    remaining = 16 - len(arg)

    return "_" * remaining + arg


def __runner(arg):
    if not os.path.isdir(os.path.join(conf.STUBS_FOLDER, arg)):
        raise argparse.ArgumentTypeError("Runner does not exist")

    return arg


def __log_level(arg):
    arg = arg.lower()

    if arg == "critical":
        return logging.CRITICAL
    if arg == "error":
        return logging.ERROR
    if arg == "warning":
        return logging.WARNING
    if arg == "info":
        return logging.INFO
    if arg == "debug":
        return logging.DEBUG
    if arg == "notset":
        return logging.NOTSET

    raise argparse.ArgumentTypeError("Invalid log level")


def __input_dir(arg):
    if os.path.isdir(arg):
        return arg
    else:
        raise argparse.ArgumentTypeError("Input dir does not exist")


def __output_dir(arg):
    if not os.path.exists(arg):
        return arg
    else:
        raise argparse.ArgumentTypeError("Output dir {} already exists".format(arg))


def __module_info(arg):
    if not os.path.exists(arg):
        return arg
    else:
        raise argparse.ArgumentTypeError("Output file {} already exists".format(arg))


def __generate_key(length):
    return os.urandom(length)


def __sp_key(arg):
    if os.path.exists(arg):
        return arg
    else:
        raise argparse.ArgumentTypeError("ra_sp public key file does not exist")
