from __future__ import division
import os
import json
import numpy as np
import logging

class TestError(Exception):
    pass

class Factor(object):
    dic = {}

    def __init__(self, out_file=None, his_file=None):
        '''
        the simplest way to persist records is plain file.
        '''
        self.out_file = out_file
        self.his_file = "history/" + out_file if his_file is None else his_file
        self.records = []

    def add_record(self, rcd):
        self.records.append(rcd)

    def evaluate(self):
        ''' Run the evaluation based on the records collected and history records. '''
        raise NotImplementedError

    def persist(self):
        ''' Persist the evalution result in some way. '''
        raise NotImplementedError

    def error_info(self):
        ''' Error information, will write to a log file. '''
        raise NotImplementedError

    # def error_info_in_html(self):
    #     ''' Error infomation, will place in a HTML page or email.'''
    #     raise NotImplementedError

    @staticmethod
    def __register__(factor):
        '''
        factor shoud a subclass inherients Factor
        '''
        assert isinstance(factor, Factor)
        key = factor.__name__
        assert Factor.dic.setdefault(key, factor) is factor, \
            "duplicate register %s with a different class" % key


class GreaterWorseFactor(Factor):
    ''' Evaluator for any factors that large value is bad, trainning cost for example. '''

    def __init__(self, name, diff_thre):
        '''
        diff_thre: difference threshold.
        '''
        super(GreaterWorseFactor, self).__init__(out_file='%s_factor.txt' % name)
        self.name = name
        self.diff_thre = diff_thre

    def evaluate(self, root):
        cur_data = load_records_from(pjoin(root, self.out_file))
        his_data = load_records_from(pjoin(root, self.his_file))
        diff = cur_data - his_data
        larger = diff > 0
        ratios = diff[larger] / his_data[larger]
        logging.info('evaluation diff ratio: %s' % str(ratios))
        return not (ratios > self.diff_thre).any()

    def persist(self):
        lines = []
        is_iterable = False
        if self.records:
            try:
                is_iterable = iter(self.records[0]) is not None
            except Exception as e:
                pass
        for rcd in self.records:
            if not is_iterable: rcd = [rcd]
            rcd = np.array(rcd)
            rcd = rcd.tolist()
            lines.append(json.dumps(rcd))

        # empty records still needs to create an empty file.
        with open(self.out_file, 'w') as f:
            f.write('\n'.join(lines))

    @property
    def error_info(self):
        return "Test [{name}] failed, some records changed too much.".format(
            name=self.name)

CostFactor = GreaterWorseFactor
DurationFactor = GreaterWorseFactor


def load_records_from(file):
    # each line of the data format is
    #     <json of record>
    # for example, a real record might be:
    #     [[0.1, 0.3], [0.4, 0.2]]
    datas = []
    with open(file) as f:
        for line in f.readlines():
            data = json.loads(line.strip())
            datas.append(np.array(data))
    return np.array(datas)

pjoin = os.path.join
