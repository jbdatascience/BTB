import logging

from btb.selection.ucb1 import UCB1

# the minimum number of scores that each choice must have in order to use
# best-K optimizations. If not all choices meet this threshold, default UCB1
# selection will be used.
K_MIN = 2

logger = logging.getLogger('btb')


class RecentKReward(UCB1):
    def __init__(self, choices, **kwargs):
        """
        Needs:
            k: number of best scores to consider
        """
        super(RecentKReward, self).__init__(choices, **kwargs)
        self.k = kwargs.pop('k', K_MIN)

    def compute_rewards(self, scores):
        """ Retain the K most recent scores, and replace the rest with zeros """
        for i in range(len(scores)):
            if i >= self.k:
                scores[i] = 0.
        return scores

    def select(self, choice_scores):
        """
        Keeps the choice counts intact but only uses the top k learner's
        scores for usage in rewards for the bandit calculation
        """
        # if we don't have enough scores to do K-selection, fall back to UCB1
        min_num_scores = min([len(s) for s in choice_scores.values()])
        if min_num_scores >= K_MIN:
            logger.info('RecentK: using Best K bandit selection')
            reward_func = self.compute_rewards
        else:
            logger.warn('RecentK: Not enough choices to do K-selection; using plain UCB1')
            reward_func = super(RecentKReward, self).compute_rewards

        choice_rewards = {}
        for choice, scores in choice_scores.items():
            if choice not in self.choices:
                continue
            choice_rewards[choice] = reward_func(scores)

        return self.bandit(choice_rewards)


class RecentKVelocity(RecentKReward):
    def compute_rewards(self, scores):
        """
        Compute the "velocity" of (average distance between) the k+1 most recent
        scores. Return a list with those k velocities padded out with zeros so
        that the count remains the same.
        """
        # take the k + 1 most recent scores so we can get k velocities
        recent_scores = scores[:-self.k - 2:-1]
        velocities = [recent_scores[i] - recent_scores[i + 1] for i in
                      range(len(recent_scores) - 1)]
        # pad the list out with zeros, so the length of the list is
        # maintained
        zeros = (len(scores) - self.k) * [0]
        return velocities + zeros
