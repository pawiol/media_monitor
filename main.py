import tvpinfo
import logging
import sys

def main():

    logging.basicConfig(filename= 'mmonitor.log',
                        format='%(asctime)s %(name)13s %(levelname)8s: ' +
                               '%(message)s',
                        level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.info('Starting script')

    insta_usr = sys.argv[1]
    isnta_pass = sys.argv[2]

    try:
        logging.debug('Starting MMonitor')

        tvp_info = tvpinfo.TVPInfo(crawler_name='tvp_info',
                                   url='http://www.tvp.info',
                                   insta_usr=insta_usr,
                                   isnta_pass=isnta_pass)
        tvp_info.get_data()

        logging.debug('Finished MMonitor')
    except:
        logging.exception('MMonitor')

    logging.info('Finished script')


if __name__ == '__main__':

    main()