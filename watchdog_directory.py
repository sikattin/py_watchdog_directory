# -*- coding: utf-8 -*-
import os
import re
import time
import sys
import glob
import shutil
import smtplib
from configparser import ConfigParser
from email.message import EmailMessage
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from mylogger.factory import RotationLoggerFactory


CONF_NAME = "watchdog_dir.conf"
LOGPATH = '/var/log/watchdog_dir.log'
SMTPHOST = 'xxx.xxx.xxx.xxx'


class FTPEventHandler(FileSystemEventHandler):
    """イベントハンドラ
    
    Args:
        FileSystemEventHandler ([type]): [description]
    """
    def __init__(self,
                 target_dir,
                 logger=None,
                 loglevel=20,
                 **kwargs
        ):
        """constructor
        
        Args:
            target_dir (str): target directory to observe.
            logger (optional): Defaults to None: logger object.
            loglevel (int, optional): Defaults to 20: loglevel of logging.
        """

        super(FTPEventHandler, self).__init__()
        self.kwargs = kwargs
        self.target_dir = target_dir
        self._logger = logger
        self._smtp = smtplib.SMTP(SMTPHOST)
        if self._logger is None:
            if not os.path.isdir(os.path.dirname(LOGPATH)):
                try:
                    os.mkdir()
                except:
                    print("can't create log directory.check error messages.")
            rotlogger_fac = RotationLoggerFactory(loglevel=loglevel)
            self._logger = rotlogger_fac.create(LOGPATH, max_bytes=100000)
            print("write log in {}".format(LOGPATH))

    def on_created(self, event):
        """[summary]
        
        Args:
            event ([type]): [description]
        """
        filename = os.path.basename(event.src_path)
        # ~coding process on the file created~
        print("ファイル {} が作成されました。".format(filename))

    def on_modified(self, event):
        """[summary]
        
        Args:
            event ([type]): [description]
        """

        filepath = event.src_path
        filename = os.path.basename(filepath)
        # ~coding process on the file modified~
        print("ファイル {} が変更されました。".format(filename))

    def on_deleted(self, event):
        """[summary]
        
        Args:
            event ([type]): [description]
        """
        filepath = event.src_path
        filename = os.path.basename(filepath)
        # ~coding process on the file deleted~
        print("ファイル {} が削除されました。".format(filename))

    def on_moved(self, event):
        """[summary]
        
        Args:
            event ([type]): [description]
        """
        filepath = event.src_path
        filename = os.path.basename(filepath)
        # ~coding process on the file moved~
        print("ファイル {0} が {1} に移動しました。".format(filename, event.dst_path))

    def _send_mail(self, subject: str, mailbody: str):
        """send mail
        
        Args:
            subject (str): Subject of mail
            mailbody (str): Body of mail
        """
        self._smtp.ehlo()
        msg = EmailMessage()
        msg.set_content(mailbody)
        msg['Subject'] = '[watchdog_dir] {}'.format(subject)
        msg['From'] = self.kwargs['MAIL']['FROM']
        msg['To'] = self.kwargs['MAIL']['TO']
        msg['Cc'] = self.kwargs['MAIL']['CC']
        self._smtp.send_message(msg)


if __name__ == '__main__':
    def _get_pylibdir():
        import watchdog_dir

        inst_dir = os.path.split(watchdog_dir.__file__)[0]
        return inst_dir
    
    def _is_existed_conf(path: list):
        if len(path) == 1:
            return True
        else:
            return False

    def _get_confpath():
        # get config file path
        pylib_path = _get_pylibdir()
        conf_dir = os.path.join(pylib_path, 'config')
        conf_path = glob.glob(os.path.join(conf_dir, '*.conf'))
        return conf_path

    def _is_exists_conf(config: ConfigParser):
        # check whether config file does exists.
        path = _get_confpath()
        if len(path) == 1:
            conf_path = path[0]
            return conf_path
        else:
            sys.stderr.write("config file does not detected or exists multiple."
                            "please create .conf file of ini format on {}".format(conf_dir))
            config['MAIL'] = {'FROM': '', 'TO': '', 'CC': ''}
            conf_dir = os.path.join(_get_pylibdir(), 'config')
            try:
                with open(os.path.join(conf_dir, CONF_NAME)) as f:
                    config.write(f)
            except Exception as e:
                print("raised exception while creating config file. due to {}. create manually yourself.".format(e))
            else:
                return False

    import argparse

    config = ConfigParser()

    description = 'observe specify directory.'
    epilog = 'example\nwatchdog_directory '

    argparser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                        description=description,
                                        epilog=epilog)
    argparser.add_argument('-c', '--config',
                           type=str,
                           required=False,
                           default=_is_exists_conf(config),
                           help='config file path. defult path is {}'.format(_is_exists_conf(config))
    )
    argparser.add_argument('-d', '--directory',
                           type=str,
                           required=False,
                           default=os.path.dirname(os.path.abspath(__file__)),
                           help='the target directory path to observe.\n'
                                'default path is execution path.'
    )
    argparser.add_argument('-l', '--loglevel',
                           type=int,
                           required=False,
                           default=20,
                           help='log level. must be set integer value 10 ~ 50.\n'
                                'default is INFO(20). 10:DEBUG, 20:INFO, 30:WARNING, 40:ERROR, 50:CRITICAL'
    )
    argparser.add_argument('-L', '--logpath',
                           type=str,
                           required=False,
                           default=LOGPATH,
                           help='log file path. write log in /var/log/watchdog_dir/watchdog_dir.log by default.'
    )
    args = argparser.parse_args()

    log_basedir = os.path.dirname(args.logpath)
    log_logfile = os.path.basename(args.logpath)
    target_dir = r"{}".format(args.directory)

    # get config file path
    conf_path = args.config
    if not conf_path:
        print("Please retry after configure config file {}"
              .format(os.path.join(_get_pylibdir(), 'config')))
        sys.exit()

    # parse config file
    try:
        config.read(conf_path)
    except Exception as e:
        print(e)
        sys.stderr.write("failed to read the config file {}.".format(conf_path))
        sys.exit()

    # create log directory
    if not os.path.isdir(log_basedir):
        try:
            os.mkdir()
        except:
            print("can't create log directory.check error messages.")
            
    # create logger
    rotlogger_fac = RotationLoggerFactory(loglevel=args.loglevel)
    _logger = rotlogger_fac.create(args.logpath, max_bytes=100000)
    print("write log in {}".format(args.logpath))

    print("target directory... {}".format(target_dir))
    period = '.'
    count = 0

    event_handler = FTPEventHandler(target_dir,
                                    logger=_logger,
                                    **config)
    observer = Observer()
    observer.schedule(event_handler, target_dir, recursive=True)
    observer.start()
    print("監視中",)
    while True:
        try:
            time.sleep(1)
            print("{}".format(period * count), )
            count += 1
        except KeyboardInterrupt as key_e:
            observer.stop()
            raise
    observer.join()
