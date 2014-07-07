#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-

def perfometer_check_mk_gearman_server(row, check_command, perf_data):
    workers_running = 0
    jobs_waiting    = 0

    for perf in perf_data:
        if '_running' in perf[0]:
            workers_running += int(perf[1])
        elif '_waiting' in perf[0]:
            jobs_waiting += int(perf[1])

    text = "%d   %d" % (workers_running, jobs_waiting)

    return text, perfometer_logarithmic_dual(
            workers_running, "#60e0a0", jobs_waiting, "#60a0e0", 5000, 10)

perfometers["check_mk-gearman_server"] = perfometer_check_mk_gearman_server
