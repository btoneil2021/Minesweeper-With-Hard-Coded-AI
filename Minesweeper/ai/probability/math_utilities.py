import math


def log_combinations(n, k):
    """
    Calculate log of binomial coefficient: log(C(n, k))

    This avoids overflow for large numbers by working in log-space.

    Args:
        n: Total items
        k: Items to choose

    Returns:
        float: log(C(n, k)), or -inf if k > n or k < 0
    """
    if k > n or k < 0:
        return float('-inf')
    if k == 0 or k == n:
        return 0.0

    # log(C(n,k)) = log(n!) - log(k!) - log((n-k)!)
    # Use math.lgamma: lgamma(n+1) = log(n!)
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def logsumexp(log_values):
    """
    Safely compute log(sum(exp(log_values))) avoiding overflow.

    Uses the logsumexp trick: log(sum(exp(x_i))) = max(x) + log(sum(exp(x_i - max(x))))

    Args:
        log_values: List of log-space values

    Returns:
        float: log(sum(exp(log_values)))
    """
    if not log_values:
        return float('-inf')

    max_log = max(log_values)
    if max_log == float('-inf'):
        return float('-inf')

    return max_log + math.log(sum(math.exp(lv - max_log) for lv in log_values))


def weighted_average_in_log_space(log_weights, values):
    """
    Calculate weighted average: sum(weight * value) / sum(weight)

    Works in log-space to avoid overflow with large weights.

    Args:
        log_weights: List of log(weight) values
        values: List of corresponding values (in normal space)

    Returns:
        float: Weighted average in normal space
    """
    if not log_weights or not values or len(log_weights) != len(values):
        return 0.0

    max_log_weight = max(log_weights)

    # Calculate sum(weight * value) in normal space after adjusting weights
    numerator = sum(math.exp(log_weights[i] - max_log_weight) * values[i]
                   for i in range(len(log_weights)))

    # Calculate sum(weight)
    denominator = sum(math.exp(lw - max_log_weight) for lw in log_weights)

    if denominator == 0:
        return 0.0

    return numerator / denominator
