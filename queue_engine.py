def rank_and_explain_queue(patient_list):
    """
    Sorts patients by CPS descending. When two consecutive patients have
    a CPS difference < 2.0, the one with the longer waiting time is
    prioritized. Adds an 'explanation' field to every patient dict.
    """
    # Initial sort by CPS descending
    queue = sorted(patient_list, key=lambda p: p['CPS'], reverse=True)

    # Bubble-pass tie-breaker: swap adjacent patients within 2.0 CPS
    # points if the later one has a longer waiting time.
    n = len(queue)
    swapped = True
    while swapped:
        swapped = False
        for i in range(n - 1):
            current = queue[i]
            nxt = queue[i + 1]
            if abs(current['CPS'] - nxt['CPS']) < 2.0:
                if nxt['Waiting Time'] > current['Waiting Time']:
                    queue[i], queue[i + 1] = nxt, current
                    swapped = True

    # Generate explanation strings
    for idx, patient in enumerate(queue):
        rank = idx + 1
        cps = patient['CPS']
        explanation = (
            f"Rank #{rank}: Score {cps} "
            f"(Severity: 45%, Survival: 35%, Wait: 20%)."
        )

        if idx > 0:
            prev = queue[idx - 1]
            if abs(prev['CPS'] - cps) < 2.0 and patient['Waiting Time'] > prev['Waiting Time']:
                wait_diff = patient['Waiting Time'] - prev['Waiting Time']
                explanation += (
                    f" Tie-broken over Patient #{prev['ID']} "
                    f"due to {wait_diff} mins longer wait time."
                )

        patient['explanation'] = explanation

    return queue