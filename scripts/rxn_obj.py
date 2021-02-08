""" update the TS
"""

import os
import automol
import autofile
import trans


PFX = '/lcrc/project/PACC/AutoMech/data/save/'


def rewrite():
    """ rewrite graph and TS files
    """

    bad_ts = []

    cnf_managers = autofile.fs.manager(
        PFX, ['REACTION', 'THEORY', 'TRANSITION STATE'], 'CONFORMER')

    for cnf_fs in cnf_managers:
        for locs in cnf_fs[-1].existing():
            cnf_path = cnf_fs[-1].path(locs)
            zma_fs = autofile.fs.zmatrix(cnf_path)
            zma_path = zma_fs[-1].path((0,))

            trans_exists = _exists(zma_path, 'trans')
            rcts_gra_exists = _exists(zma_path, 'rctgra')
            if trans_exists and rcts_gra_exists:
                tra = _read(zma_path, 'trans')
                rcts_gra = _read(zma_path, 'rctgra')
                _build_new(zma_fs, tra, rcts_gra)
            else:
                bad_ts.append(cnf_path)


def rewrite_test():
    """ rewrite graph and TS files
    """

    conf_path = '/lcrc/project/PACC/AutoMech/data/save/RXN/C3H5.H2/ZJMQNRRDFSUTLJ/0_0/2_1/UHFFFAOYSA-N/C3H6.H/MULOCOKNWSNATD/0_0/1_2/UHFFFAOYSA-N/2/u-ulpJU/TS/CONFS/cLSJV7-VTOQLd/'
    zma_path = '/lcrc/project/PACC/AutoMech/data/save/RXN/C3H5.H2/ZJMQNRRDFSUTLJ/0_0/2_1/UHFFFAOYSA-N/C3H6.H/MULOCOKNWSNATD/0_0/1_2/UHFFFAOYSA-N/2/u-ulpJU/TS/CONFS/cLSJV7-VTOQLd/Z/00'

    zma_fs = autofile.fs.zmatrix(conf_path)
    trans_exists = _exists(zma_path, 'trans')
    rcts_gra_exists = _exists(zma_path, 'rctgra')
    if trans_exists and rcts_gra_exists:
        print('here')
        trans = _read(zma_path, 'trans')
        rcts_gra = _read(zma_path, 'rctgra')
        _build_new(zma_fs, trans, rcts_gra)
    else:
        # bad_ts.append(cnf_path)
        pass


def _exists(zma_path, obj):
    """
    """
    if obj == 'trans':
        name = 'zmat.t.yaml'
    elif obj == 'rctgra':
        name = 'zmat.g.yaml'
    fname = os.path.join(zma_path, name)

    return os.path.exists(fname)


def _read(zma_path, obj):
    """
    """
    if obj == 'trans':
        name = 'zmat.t.yaml'
    elif obj == 'rctgra':
        name = 'zmat.g.yaml'
    elif obj == 'zma':
        name = 'zmat.zmat'
    fname = os.path.join(zma_path, name)
    with open(fname) as fobj:
        file_str = fobj.read()

    if obj == 'trans':
        ret = _trans(file_str)
    elif obj == 'rctgra':
        ret = _graph(file_str)

    return ret


def _trans(tra_str):
    """ read a chemical transformation from a string
    """
    tra = trans.old_from_string(tra_str)
    return tra


def _graph(gra_str):
    """ read a molecular graph from a string
    """
    gra = automol.graph.from_string(gra_str)
    return gra


def _build_new(zma_fs, tra, rcts_gra):
    """ build new line
    """

    # 1. Get the keys and build the ts graph
    frm_bnd_keys = trans.old_formed_bond_keys(tra)
    brk_bnd_keys = trans.old_broken_bond_keys(tra)

    tsg1 = automol.graph.ts.graph(rcts_gra, frm_bnd_keys, brk_bnd_keys)

    # 2. Reclassify the reaction and get a new forward graph
    rxn = _reclassify(tra, rcts_gra)
    tsg2 = rxn.forward_ts_graph

    # 3 Obtain isomorphism between the graphs
    key_dct = automol.graph.full_isomorphism(tsg2, tsg1)

    # 4. Relabel the reaction with old keys
    rxn = automol.reac.relabel(rxn, key_dct)

    # 5. write the new files
    zma = zma_fs[-1].file.zmatrix.read([0])
    print(automol.zmat.string(zma))
    print(rxn)
    # zma_fs[-1].file.reac.write(rxn)

    return rxn


def _reclassify(tra, rcts_gra):
    """ reclassify the reaction
    """

    # 1. Get prd graph
    prds_gra = trans.apply(tra, rcts_gra)

    rct_gras = automol.graph.connected_components(rcts_gra)
    prd_gras = automol.graph.connected_components(prds_gra)

    rct_geos = list(map(automol.graph.geometry, rct_gras))
    prd_geos = list(map(automol.graph.geometry, prd_gras))

    rct_gras, _ = automol.graph.standard_keys_for_sequence(rct_gras)
    prd_gras, _ = automol.graph.standard_keys_for_sequence(prd_gras)

    rxns = automol.reac.find(rct_gras, prd_gras)
    rxn = rxns[0]

    rxn, rct_geos, prd_geos = (
        automol.reac.standard_keys_with_sorted_geometries(
            rxn, rct_geos, prd_geos))

    return rxn


if __name__ == '__main__':
    rewrite_test()