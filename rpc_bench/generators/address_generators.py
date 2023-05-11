from __future__ import annotations

import typing


def generate_contract_addresses(n: int) -> typing.Sequence[str]:
    import pdp.datasets.contracts

    df = pdp.datasets.contracts.query_contracts(
        columns=['contract_address'], network='ethereum'
    )
    series = '0x' + df['contract_address'].sample(n).bin.encode('hex')
    return series.to_list()


def generate_eoas(n: int) -> typing.Sequence[str]:
    raise NotImplementedError()

