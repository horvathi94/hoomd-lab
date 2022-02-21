from dataclasses import dataclass


@dataclass
class Interaction:

    p1_label: str
    p2_label: str
    epsilon: float
    sigma: float
    alpha: float


    def __post_init__(self):
        self.epsilon = float(self.epsilon)
        self.sigma = float(self.sigma)
        self.alpha = float(self.alpha)


    def as_dict(self) -> dict:
        return {self.p1_label:
            {"with": self.p2_label,
             "epsilon": self.epsilon,
             "sigma": self.sigma,
             "alpha": self.alpha,}
        }
