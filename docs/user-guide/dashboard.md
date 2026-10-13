# Dashboard

The dashboard shows the jobs submitted inside the selected date range on the selected cluster, aggregated by the binning period chosen in the sidebar.

## Binning period

Time-series charts bin jobs by their start time into days, weeks (starting Monday), months or years. `Auto` picks a period from the length of the date range.

## Empty periods

The time axis of every time-series chart covers the whole selected date range, including periods in which no job started. How an empty period is drawn depends on what the chart measures:

- Counts and sums (submitted jobs, active users, CPU, GPU and memory hours, and the stacked duration and waiting-time shares) show zero.
- Averages, percentiles and efficiencies (waiting time and job duration over time and their trend bands, CPU and memory efficiency) have no value in an empty period and leave a gap in the line, so the line is not drawn through periods that were never measured.

A period whose jobs all lack the measured column, for example CPU efficiency before the agent reported `CPUUsedHours`, is also drawn as a gap.

Histograms of per-period values (jobs per period, hours per period) only use periods in which at least one job started.

## Switching cluster

Changing the cluster in the sidebar keeps the other selections. The date range is kept and only moved inside the new cluster's data range when it falls outside it. Binning period, colour dimension, account name format and the node chart options are unchanged. Selected partitions, accounts, users, QOS values and states are kept where the new cluster has them; a value the new cluster does not have is dropped, because it could not be seen or unticked in the sidebar.
