# Turns cell ID into eNB and sector ID
def decompose_cid(cid: int) -> (str, str):
    binstr = bin(cid)
    sid = str(int(binstr[-8:], 2))
    nid = str(int(binstr[:-8], 2))

    return nid, sid
