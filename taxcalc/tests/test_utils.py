"""
Tests of Tax-Calculator utility functions.
"""
# CODING-STYLE CHECKS:
# pycodestyle test_utils.py
# pylint --disable=locally-disabled test_utils.py
#
# pylint: disable=missing-docstring,no-member,protected-access,too-many-lines

import numpy as np
import pandas as pd
import pytest
# pylint: disable=import-error
from taxcalc import Policy, Records, Calculator
from taxcalc.utils import (DIST_VARIABLES,
                           DIST_TABLE_COLUMNS, DIST_TABLE_LABELS,
                           DIFF_VARIABLES,
                           DIFF_TABLE_COLUMNS, DIFF_TABLE_LABELS,
                           SOI_AGI_BINS,
                           create_distribution_table, create_difference_table,
                           weighted_count_lt_zero, weighted_count_gt_zero,
                           weighted_count, weighted_sum,
                           add_income_table_row_variable,
                           add_quantile_table_row_variable,
                           read_egg_csv, read_egg_json,
                           bootstrap_se_ci,
                           nonsmall_diffs,
                           quantity_response)


DATA = [[1.0, 2, 'a'],
        [-1.0, 4, 'a'],
        [3.0, 6, 'a'],
        [2.0, 4, 'b'],
        [3.0, 6, 'b']]

WEIGHT_DATA = [[1.0, 2.0, 10.0],
               [2.0, 4.0, 20.0],
               [3.0, 6.0, 30.0]]

DATA_FLOAT = [[1.0, 2, 'a'],
              [-1.0, 4, 'a'],
              [0.0000000001, 3, 'a'],
              [-0.0000000001, 1, 'a'],
              [3.0, 6, 'a'],
              [2.0, 4, 'b'],
              [0.0000000001, 3, 'b'],
              [-0.0000000001, 1, 'b'],
              [3.0, 6, 'b']]


def xtest_validity_of_name_lists():
    assert len(DIST_TABLE_COLUMNS) == len(DIST_TABLE_LABELS)
    Records.read_var_info()
    assert set(DIST_VARIABLES).issubset(Records.CALCULATED_VARS | {'weight'})
    extra_vars_set = set(['num_returns_StandardDed',
                          'num_returns_ItemDed',
                          'num_returns_AMT'])
    assert (set(DIST_TABLE_COLUMNS) - set(DIST_VARIABLES)) == extra_vars_set


def xtest_create_tables(pit_subsample):
    # pylint: disable=too-many-statements,too-many-branches
    # create a current-law Policy object and Calculator object calc1
    rec = Records(data=pit_subsample)
    pol = Policy()
    calc1 = Calculator(policy=pol, records=rec)
    calc1.calc_all()
    # create a policy-reform Policy object and Calculator object calc2
    reform = {2017: {'_rate2': [0.06]}}
    pol.implement_reform(reform)
    calc2 = Calculator(policy=pol, records=rec)
    calc2.calc_all()

    test_failure = False

    # test creating various difference tables

    diff = create_difference_table(calc1.dataframe(DIFF_VARIABLES),
                                   calc2.dataframe(DIFF_VARIABLES),
                                   'standard_income_bins', 'combined')
    assert isinstance(diff, pd.DataFrame)
    tabcol = 'pc_aftertaxinc'
    expected = [np.nan,
                np.nan,
                -0.24,
                -0.79,
                -0.81,
                -0.55,
                -0.77,
                -0.69,
                -0.70,
                -0.67,
                -0.27,
                -0.11,
                -0.06,
                -0.58]
    if not np.allclose(diff[tabcol].values, expected,
                       atol=0.005, rtol=0.0, equal_nan=True):
        test_failure = True
        print('diff xbin', tabcol)
        for val in diff[tabcol].values:
            print('{:.2f},'.format(val))

    diff = create_difference_table(calc1.dataframe(DIFF_VARIABLES),
                                   calc2.dataframe(DIFF_VARIABLES),
                                   'weighted_deciles', 'combined')
    assert isinstance(diff, pd.DataFrame)
    tabcol = 'tot_change'
    expected = [0,
                0,
                254095629,
                2544151690,
                2826173357,
                2539574809,
                4426339426,
                5178198524,
                6277367974,
                8069273960,
                10572653961,
                10269542170,
                52957371499,
                6188055374,
                3497187245,
                584299551]
    if not np.allclose(diff[tabcol].values, expected,
                       atol=0.51, rtol=0.0):
        test_failure = True
        print('diff xdec', tabcol)
        for val in diff[tabcol].values:
            print('{:.0f},'.format(val))

    tabcol = 'share_of_change'
    expected = [0.00,
                0.00,
                0.48,
                4.80,
                5.34,
                4.80,
                8.36,
                9.78,
                11.85,
                15.24,
                19.96,
                19.39,
                100.00,
                11.68,
                6.60,
                1.10]
    if not np.allclose(diff[tabcol].values, expected,
                       atol=0.005, rtol=0.0):
        test_failure = True
        print('diff xdec', tabcol)
        for val in diff[tabcol].values:
            print('{:.2f},'.format(val))

    tabcol = 'pc_aftertaxinc'
    expected = [np.nan,
                np.nan,
                -0.26,
                -0.96,
                -0.74,
                -0.52,
                -0.75,
                -0.71,
                -0.68,
                -0.71,
                -0.71,
                -0.34,
                -0.58,
                -0.61,
                -0.30,
                -0.07]
    if not np.allclose(diff[tabcol].values, expected,
                       atol=0.005, rtol=0.0, equal_nan=True):
        test_failure = True
        print('diff xdec', tabcol)
        for val in diff[tabcol].values:
            print('{:.2f},'.format(val))

    # test creating various distribution tables

    dist, _ = calc2.distribution_tables(None, 'weighted_deciles')
    assert isinstance(dist, pd.DataFrame)
    tabcol = 'iitax'
    expected = [0,
                0,
                -1818680093,
                1971755805,
                5010676892,
                6746034269,
                17979713134,
                26281107130,
                35678824858,
                82705314943,
                148818900147,
                734130905355,
                1057504552440,
                152370476198,
                234667184101,
                347093245055]
    if not np.allclose(dist[tabcol].values, expected,
                       atol=0.5, rtol=0.0):
        test_failure = True
        print('dist xdec', tabcol)
        for val in dist[tabcol].values:
            print('{:.0f},'.format(val))

    tabcol = 'num_returns_ItemDed'
    expected = [0,
                0,
                357019,
                1523252,
                2463769,
                2571339,
                4513934,
                5278763,
                6299826,
                7713038,
                11001450,
                13125085,
                54847474,
                6188702,
                5498415,
                1437967]
    if not np.allclose(dist[tabcol].tolist(), expected,
                       atol=0.5, rtol=0.0):
        test_failure = True
        print('dist xdec', tabcol)
        for val in dist[tabcol].values:
            print('{:.0f},'.format(val))

    tabcol = 'expanded_income'
    expected = [0,
                0,
                105927980655,
                294023675202,
                417068113194,
                528376852001,
                658853731628,
                818158430558,
                1037838578149,
                1324689584778,
                1788101751565,
                4047642990187,
                11020681687917,
                1286581399758,
                1511884268254,
                1249177322176]
    if not np.allclose(dist[tabcol].tolist(), expected,
                       atol=0.5, rtol=0.0):
        test_failure = True
        print('dist xdec', tabcol)
        for val in dist[tabcol].values:
            print('{:.0f},'.format(val))

    tabcol = 'aftertax_income'
    expected = [0,
                0,
                97735000432,
                261911925318,
                378049091828,
                485619641327,
                586208937799,
                722979233740,
                919208533243,
                1130705156084,
                1473967098213,
                2994484618211,
                9050869236196,
                1002450732282,
                1147596725957,
                844437159972]
    if not np.allclose(dist[tabcol].tolist(), expected,
                       atol=0.5, rtol=0.0):
        test_failure = True
        print('dist xdec', tabcol)
        for val in dist[tabcol].values:
            print('{:.0f},'.format(val))

    dist, _ = calc2.distribution_tables(None, 'standard_income_bins')
    assert isinstance(dist, pd.DataFrame)
    tabcol = 'iitax'
    expected = [0,
                0,
                -544908512,
                -140959365,
                3354006293,
                9339571323,
                18473567840,
                55206201916,
                89276157367,
                297973932010,
                290155554334,
                99528466942,
                194882962290,
                1057504552440]
    if not np.allclose(dist[tabcol], expected,
                       atol=0.5, rtol=0.0):
        test_failure = True
        print('dist xbin', tabcol)
        for val in dist[tabcol].values:
            print('{:.0f},'.format(val))

    tabcol = 'num_returns_ItemDed'
    expected = [0,
                0,
                60455,
                1107780,
                2366845,
                3460607,
                4837397,
                10090391,
                8850784,
                17041135,
                6187168,
                532925,
                311987,
                54847474]
    if not np.allclose(dist[tabcol].tolist(), expected,
                       atol=0.5, rtol=0.0):
        test_failure = True
        print('dist xbin', tabcol)
        for val in dist[tabcol].values:
            print('{:.0f},'.format(val))

    if test_failure:
        assert 1 == 2


def test_diff_count_precision():
    """
    Estimate bootstrap standard error and confidence interval for count
    statistics ('tax_cut' and 'tax_inc') in difference table generated
    using puf.csv input data taking no account of tbi privacy fuzzing and
    assuming all filing units in each bin have the same weight.  These
    assumptions imply that the estimates produced here are likely to
    over-estimate the precision of the count statistics.

    Background information on unweighted number of filing units by bin:

    DECILE BINS:
    0   16268
    1   14897
    2   13620
    3   15760
    4   16426
    5   18070
    6   18348
    7   19352
    8   21051
    9   61733 <--- largest unweighted bin count
    A  215525

    STANDARD BINS:
    0    7081 <--- negative income bin is dropped in TaxBrain display
    1   19355
    2   22722
    3   20098
    4   17088
    5   14515
    6   24760
    7   15875
    8   25225
    9   15123
    10  10570 <--- smallest unweighted bin count
    11  23113 <--- second largest unweighted WEBAPP bin count
    A  215525

    Background information on Trump2017.json reform used in TaxBrain run 16649:

    STANDARD bin 10 ($500-1000 thousand) has weighted count of 1179 thousand;
                    weighted count of units with tax increase is 32 thousand.

    So, the mean weight for all units in STANDARD bin 10 is 111.5421 and the
    unweighted number with a tax increase is 287 assuming all units in that
    bin have the same weight.  (Note that 287 * 111.5421 is about 32,012.58,
    which rounds to the 32 thousand shown in the TaxBrain difference table.)

    STANDARD bin 11 ($1000+ thousand) has weighted count of 636 thousand;
                    weighted count of units with tax increase is 27 thousand.

    So, the mean weight for all units in STANDARD bin 11 is about 27.517 and
    the unweighted number with a tax increase is 981 assuming all units in
    that bin have the same weight.  (Note that 981 * 27.517 is about 26,994.18,
    which rounds to the 27 thousand shown in the TaxBrain difference table.)
    """
    dump = False  # setting to True implies results printed and test fails
    seed = 123456789
    bs_samples = 1000
    alpha = 0.025  # implies 95% confidence interval
    # compute stderr and confidence interval for STANDARD bin 10 increase count
    data_list = [111.5421] * 287 + [0.0] * (10570 - 287)
    assert len(data_list) == 10570
    data = np.array(data_list)
    assert (data > 0).sum() == 287
    data_estimate = np.sum(data) * 1e-3
    assert abs((data_estimate / 32) - 1) < 0.0005
    bsd = bootstrap_se_ci(data, seed, bs_samples, np.sum, alpha)
    stderr = bsd['se'] * 1e-3
    cilo = bsd['cilo'] * 1e-3
    cihi = bsd['cihi'] * 1e-3
    if dump:
        res = '{}EST={:.1f} B={} alpha={:.3f} se={:.2f} ci=[ {:.2f} , {:.2f} ]'
        print(
            res.format('STANDARD-BIN10: ',
                       data_estimate, bs_samples, alpha, stderr, cilo, cihi)
        )
    assert abs((stderr / 1.90) - 1) < 0.0008
    # NOTE: a se of 1.90 thousand implies that when comparing the difference
    #       in the weighted number of filing units in STANDARD bin 10 with a
    #       tax increase, the difference statistic has a bigger se (because
    #       the variance of the difference is the sum of the variances of the
    #       two point estimates).  So, in STANDARD bin 10 if the point
    #       estimates both had se = 1.90, then the difference in the point
    #       estimates has has a se = 2.687.  This means that the difference
    #       would have to be over 5 thousand in order for there to be high
    #       confidence that the difference was different from zero in a
    #       statistically significant manner.
    #       Or put a different way, a difference of 1 thousand cannot be
    #       accurately detected while a difference of 10 thousand can be
    #       accurately detected.
    assert abs((cilo / 28.33) - 1) < 0.0012
    assert abs((cihi / 35.81) - 1) < 0.0012
    # compute stderr and confidence interval for STANDARD bin 11 increase count
    data_list = [27.517] * 981 + [0.0] * (23113 - 981)
    assert len(data_list) == 23113
    data = np.array(data_list)
    assert (data > 0).sum() == 981
    data_estimate = np.sum(data) * 1e-3
    assert abs((data_estimate / 27) - 1) < 0.0005
    bsd = bootstrap_se_ci(data, seed, bs_samples, np.sum, alpha)
    stderr = bsd['se'] * 1e-3
    cilo = bsd['cilo'] * 1e-3
    cihi = bsd['cihi'] * 1e-3
    if dump:
        res = '{}EST={:.1f} B={} alpha={:.3f} se={:.2f} ci=[ {:.2f} , {:.2f} ]'
        print(
            res.format('STANDARD-BIN11: ',
                       data_estimate, bs_samples, alpha, stderr, cilo, cihi)
        )
    assert abs((stderr / 0.85) - 1) < 0.0040
    # NOTE: a se of 0.85 thousand implies that when comparing the difference
    #       in the weighted number of filing units in STANDARD bin 11 with a
    #       tax increase, the difference statistic has a bigger se (because
    #       the variance of the difference is the sum of the variances of the
    #       two point estimates).  So, in STANDARD bin 11 if point estimates
    #       both had se = 0.85, then the difference in the point estimates has
    #       has a se = 1.20.  This means that the difference would have to be
    #       over 2.5 thousand in order for there to be high confidence that the
    #       difference was different from zero in a statistically significant
    #       manner.
    #       Or put a different way, a difference of 1 thousand cannot be
    #       accurately detected while a difference of 10 thousand can be
    #       accurately detected.
    assert abs((cilo / 25.37) - 1) < 0.0012
    assert abs((cihi / 28.65) - 1) < 0.0012
    # fail if doing dump
    assert not dump


def test_weighted_count_lt_zero():
    df1 = pd.DataFrame(data=DATA, columns=['tax_diff', 'weight', 'label'])
    grped = df1.groupby('label')
    diffs = grped.apply(weighted_count_lt_zero, 'tax_diff')
    exp = pd.Series(data=[4, 0], index=['a', 'b'])
    exp.index.name = 'label'
    pd.util.testing.assert_series_equal(exp, diffs)
    df2 = pd.DataFrame(data=DATA_FLOAT, columns=['tax_diff', 'weight',
                                                 'label'])
    grped = df2.groupby('label')
    diffs = grped.apply(weighted_count_lt_zero, 'tax_diff')
    exp = pd.Series(data=[4, 0], index=['a', 'b'])
    exp.index.name = 'label'
    pd.util.testing.assert_series_equal(exp, diffs)


def test_weighted_count_gt_zero():
    df1 = pd.DataFrame(data=DATA, columns=['tax_diff', 'weight', 'label'])
    grped = df1.groupby('label')
    diffs = grped.apply(weighted_count_gt_zero, 'tax_diff')
    exp = pd.Series(data=[8, 10], index=['a', 'b'])
    exp.index.name = 'label'
    pd.util.testing.assert_series_equal(exp, diffs)
    df2 = pd.DataFrame(data=DATA, columns=['tax_diff', 'weight', 'label'])
    grped = df2.groupby('label')
    diffs = grped.apply(weighted_count_gt_zero, 'tax_diff')
    exp = pd.Series(data=[8, 10], index=['a', 'b'])
    exp.index.name = 'label'
    pd.util.testing.assert_series_equal(exp, diffs)


def test_weighted_count():
    dfx = pd.DataFrame(data=DATA, columns=['tax_diff', 'weight', 'label'])
    grouped = dfx.groupby('label')
    diffs = grouped.apply(weighted_count)
    exp = pd.Series(data=[12, 10], index=['a', 'b'])
    exp.index.name = 'label'
    pd.util.testing.assert_series_equal(exp, diffs)


def test_weighted_sum():
    dfx = pd.DataFrame(data=DATA, columns=['tax_diff', 'weight', 'label'])
    grouped = dfx.groupby('label')
    diffs = grouped.apply(weighted_sum, 'tax_diff')
    exp = pd.Series(data=[16.0, 26.0], index=['a', 'b'])
    exp.index.name = 'label'
    pd.util.testing.assert_series_equal(exp, diffs)


EPSILON = 1e-5


def test_add_income_trow_var():
    dta = np.arange(1, 1e6, 5000)
    vdf = pd.DataFrame(data=dta, columns=['expanded_income'])
    vdf = add_income_table_row_variable(vdf, 'expanded_income', SOI_AGI_BINS)
    gdf = vdf.groupby('table_row')
    idx = 1
    for name, _ in gdf:
        assert name.closed == 'left'
        assert abs(name.right - SOI_AGI_BINS[idx]) < EPSILON
        idx += 1


def test_add_quantile_trow_var():
    dfx = pd.DataFrame(data=DATA, columns=['expanded_income', 'weight',
                                           'label'])
    dfb = add_quantile_table_row_variable(dfx, 'expanded_income',
                                          100, decile_details=False,
                                          weight_by_income_measure=False)
    bin_labels = dfb['table_row'].unique()
    default_labels = set(range(1, 101))
    for lab in bin_labels:
        assert lab in default_labels
    dfb = add_quantile_table_row_variable(dfx, 'expanded_income',
                                          100, decile_details=False)
    assert 'table_row' in dfb
    with pytest.raises(ValueError):
        dfb = add_quantile_table_row_variable(dfx, 'expanded_income',
                                              100, decile_details=True)


def xtest_dist_table_sum_row(pit_subsample):
    rec = Records(data=pit_subsample)
    calc = Calculator(policy=Policy(), records=rec)
    calc.calc_all()
    tb1 = create_distribution_table(calc.distribution_table_dataframe(),
                                    'standard_income_bins', 'expanded_income')
    tb2 = create_distribution_table(calc.distribution_table_dataframe(),
                                    'soi_agi_bins', 'expanded_income')
    assert np.allclose(tb1[-1:], tb2[-1:])


def xtest_diff_table_sum_row(pit_subsample):
    rec = Records(data=pit_subsample)
    # create a current-law Policy object and Calculator calc1
    pol = Policy()
    calc1 = Calculator(policy=pol, records=rec)
    calc1.calc_all()
    # create a policy-reform Policy object and Calculator calc2
    reform = {2017: {'_rate2': [0.06]}}
    pol.implement_reform(reform)
    calc2 = Calculator(policy=pol, records=rec)
    calc2.calc_all()
    # create two difference tables and compare their content
    tdiff1 = create_difference_table(calc1.dataframe(DIFF_VARIABLES),
                                     calc2.dataframe(DIFF_VARIABLES),
                                     'standard_income_bins', 'iitax')
    tdiff2 = create_difference_table(calc1.dataframe(DIFF_VARIABLES),
                                     calc2.dataframe(DIFF_VARIABLES),
                                     'soi_agi_bins', 'iitax')
    non_digit_cols = ['perc_inc', 'perc_cut']
    digit_cols = [c for c in list(tdiff1) if c not in non_digit_cols]
    assert np.allclose(tdiff1[digit_cols][-1:],
                       tdiff2[digit_cols][-1:])
    np.allclose(tdiff1[non_digit_cols][-1:],
                tdiff2[non_digit_cols][-1:])


def test_read_egg_csv():
    with pytest.raises(ValueError):
        read_egg_csv('bad_filename')


def test_read_egg_json():
    with pytest.raises(ValueError):
        read_egg_json('bad_filename')


def test_bootstrap_se_ci():
    # Use treated mouse data from Table 2.1 and
    # results from Table 2.2 and Table 13.1 in
    # Bradley Efron and Robert Tibshirani,
    # "An Introduction to the Bootstrap"
    # (Chapman & Hall, 1993).
    data = np.array([94, 197, 16, 38, 99, 141, 23], dtype=np.float64)
    assert abs(np.mean(data) - 86.86) < 0.005  # this is just rounding error
    bsd = bootstrap_se_ci(data, 123456789, 1000, np.mean, alpha=0.025)
    # following comparisons are less precise because of r.n. stream differences
    assert abs(bsd['se'] / 23.02 - 1) < 0.02
    assert abs(bsd['cilo'] / 45.9 - 1) < 0.02
    assert abs(bsd['cihi'] / 135.4 - 1) < 0.03


def test_table_columns_labels():
    # check that length of two lists are the same
    assert len(DIST_TABLE_COLUMNS) == len(DIST_TABLE_LABELS)
    assert len(DIFF_TABLE_COLUMNS) == len(DIFF_TABLE_LABELS)


def test_nonsmall_diffs():
    assert nonsmall_diffs(['AAA'], ['AAA', 'BBB'])
    assert nonsmall_diffs(['AaA'], ['AAA'])
    assert not nonsmall_diffs(['AAA'], ['AAA'])
    assert nonsmall_diffs(['12.3'], ['12.2'])
    assert not nonsmall_diffs(['12.3 AAA'], ['12.2 AAA'], small=0.1)
    assert nonsmall_diffs(['12.3'], ['AAA'])


def test_quantity_response():
    quantity = np.array([1.0] * 10)
    res = quantity_response(quantity,
                            price_elasticity=0,
                            aftertax_price1=None,
                            aftertax_price2=None,
                            income_elasticity=0,
                            aftertax_income1=None,
                            aftertax_income2=None)
    assert np.allclose(res, np.zeros(quantity.shape))
    one = np.ones(quantity.shape)
    res = quantity_response(quantity,
                            price_elasticity=-0.2,
                            aftertax_price1=one,
                            aftertax_price2=one,
                            income_elasticity=0.1,
                            aftertax_income1=one,
                            aftertax_income2=(one + one))
    assert not np.allclose(res, np.zeros(quantity.shape))
