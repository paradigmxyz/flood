from __future__ import annotations

import typing

import flood


default_stress_test_rates = [1, 4, 16, 64, 256, 512]
default_stress_test_duration = 30
default_spike_rates = {
    'before': 8,
    'during': 2048,
    'after': 8,
}
default_spike_durations = {
    'before': 30,
    'during': 10,
    'after': 30,
}
default_soak_test_rate = 100
default_soak_test_duration = 24 * 60 * 60


def generate_timings(
    rates: typing.Sequence[int] | None = None,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    mode: flood.LoadTestMode | None = None,
) -> tuple[typing.Sequence[int], typing.Sequence[int]]:
    """create rates and durations for test"""

    if mode is None:
        mode = 'stress'

    if mode == 'stress':
        return _generate_timings_for_stress_test(
            rates=rates,
            duration=duration,
            durations=durations,
        )
    elif mode == 'soak':
        return _generate_timings_for_soak_test(
            rates=rates,
            duration=duration,
            durations=durations,
        )
    elif mode == 'spike':
        return _generate_timings_for_spike_test(
            rates=rates,
            duration=duration,
            durations=durations,
        )
    else:
        raise Exception('unknown mode: ' + str(mode))


def _generate_timings_for_stress_test(
    rates: typing.Sequence[int] | None = None,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
) -> tuple[typing.Sequence[int], typing.Sequence[int]]:
    if rates is None:
        rates = default_stress_test_rates
    if durations is None:
        if duration is None:
            duration = default_stress_test_duration
        durations = [duration] * len(rates)
    return rates, durations


def _generate_timings_for_spike_test(
    rates: typing.Sequence[int] | None = None,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
) -> tuple[typing.Sequence[int], typing.Sequence[int]]:
    if rates is None:
        rates = [
            default_spike_rates['before'],
            default_spike_rates['during'],
            default_spike_rates['after'],
        ]
    else:
        if len(rates) == 1:
            rates = [
                default_spike_rates['before'],
                rates[0],
                default_spike_rates['after'],
            ]
        elif len(rates) == 3:
            pass
        else:
            raise Exception(
                'must specify eith a single spike rate or a [before, during, after] triplet of rates'  # noqa: E501
            )

    if duration is not None:
        durations = [
            default_spike_durations['before'],
            duration,
            default_spike_durations['after'],
        ]
    elif durations is not None:
        if len(durations) == 1:
            durations = [
                default_spike_durations['before'],
                durations[0],
                default_spike_durations['after'],
            ]
        elif len(durations) == 3:
            pass
        else:
            raise Exception(
                'must specify eith a single spike duration or a [before, during, after] triplet of rates'  # noqa: E501
            )
    else:
        durations = [
            default_spike_durations['before'],
            default_spike_durations['during'],
            default_spike_durations['after'],
        ]

    return rates, durations


def _generate_timings_for_soak_test(
    rates: typing.Sequence[int] | None = None,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
) -> tuple[typing.Sequence[int], typing.Sequence[int]]:
    if rates is not None:
        if len(rates) != 1:
            raise Exception('must specify 1 rate for soak test')
    else:
        rates = [default_soak_test_rate]

    if durations is None:
        if duration is not None:
            durations = [duration]
        else:
            durations = [default_soak_test_duration]
    else:
        if len(durations) != 1:
            raise Exception('must specify 1 duration for soak test')

    return rates, durations
