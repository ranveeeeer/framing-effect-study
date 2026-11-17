"""
The five decision problems, word for word as the students saw them.

Each problem has a sure option and a risky option with the same expected
value: the sure option is worth 1/3 of the total, and the risky option
gives a 1/3 chance of everything and a 2/3 chance of nothing.

Only the wording changes between frames:
  gain frame -> outcomes described as what is saved / kept
  loss frame -> the same outcomes described as what is lost / dies
"""

INSTRUCTIONS = (
    "Each question gives two options, A and B. Choose exactly one option. "
    "Assume all numbers and probabilities are exact, and that the outcomes "
    "will definitely happen as described. There are no right or wrong "
    "answers. Choose the option you would genuinely prefer."
)

ITEMS = {
    "health": {
        "setup": "A disease threatens 600 people in a town. You must choose one of two programs.",
        "sure": {
            "gain": "Exactly 200 people will definitely be saved.",
            "loss": "Exactly 400 people will definitely die.",
        },
        "risky": {
            "gain": "There is a probability of 1/3 (one in three) that all 600 people will be saved, and a probability of 2/3 (two in three) that no one will be saved.",
            "loss": "There is a probability of 1/3 (one in three) that no one will die, and a probability of 2/3 (two in three) that all 600 people will die.",
        },
    },
    "money": {
        "setup": "You hold ₹30,000. You must choose one of two options.",
        "sure": {
            "gain": "You will definitely keep ₹10,000.",
            "loss": "You will definitely lose ₹20,000.",
        },
        "risky": {
            "gain": "There is a probability of 1/3 (one in three) that you keep all ₹30,000, and a probability of 2/3 (two in three) that you keep nothing.",
            "loss": "There is a probability of 1/3 (one in three) that you lose nothing, and a probability of 2/3 (two in three) that you lose all ₹30,000.",
        },
    },
    "marks": {
        "setup": "You hold 30 marks in an exam. You must choose one of two preparation strategies.",
        "sure": {
            "gain": "You will definitely keep 10 marks.",
            "loss": "You will definitely lose 20 marks.",
        },
        "risky": {
            "gain": "There is a probability of 1/3 (one in three) that you keep all 30 marks, and a probability of 2/3 (two in three) that you keep none.",
            "loss": "There is a probability of 1/3 (one in three) that you lose no marks, and a probability of 2/3 (two in three) that you lose all 30 marks.",
        },
    },
    "jobs": {
        "setup": "A company has 300 jobs at risk. You must choose one of two rescue plans.",
        "sure": {
            "gain": "Exactly 100 jobs will definitely be saved.",
            "loss": "Exactly 200 jobs will definitely be lost.",
        },
        "risky": {
            "gain": "There is a probability of 1/3 (one in three) that all 300 jobs will be saved, and a probability of 2/3 (two in three) that no jobs will be saved.",
            "loss": "There is a probability of 1/3 (one in three) that no jobs will be lost, and a probability of 2/3 (two in three) that all 300 jobs will be lost.",
        },
    },
    "crops": {
        "setup": "A flood threatens a farmer's 90 acres of crops. You must choose one of two measures.",
        "sure": {
            "gain": "Exactly 30 acres will definitely be saved.",
            "loss": "Exactly 60 acres will definitely be lost.",
        },
        "risky": {
            "gain": "There is a probability of 1/3 (one in three) that all 90 acres will be saved, and a probability of 2/3 (two in three) that no acres will be saved.",
            "loss": "There is a probability of 1/3 (one in three) that no acres will be lost, and a probability of 2/3 (two in three) that all 90 acres will be lost.",
        },
    },
}

SCENARIOS = list(ITEMS.keys())

ENDINGS = {
    "direct": "Reply with only one line: Answer: A or Answer: B",
    "step_by_step": "Think it through step by step, then end your reply with a final line: Answer: A or Answer: B",
}


def build_prompt(scenario, frame, mode, order):
    """
    Build the exact text sent to a model.

    order = "sure_first"  -> A is the sure option, B is the risky one
    order = "risky_first" -> A is the risky option, B is the sure one

    Returns the prompt and a dictionary that turns the letter back into
    its meaning, e.g. {"A": "sure", "B": "risky"}.
    """
    item = ITEMS[scenario]
    sure_text = item["sure"][frame]
    risky_text = item["risky"][frame]

    if order == "sure_first":
        option_a, option_b = sure_text, risky_text
        letter_meaning = {"A": "sure", "B": "risky"}
    else:
        option_a, option_b = risky_text, sure_text
        letter_meaning = {"A": "risky", "B": "sure"}

    prompt = (
        f"{INSTRUCTIONS}\n\n"
        f"{item['setup']}\n"
        f"A: {option_a}\n"
        f"B: {option_b}\n\n"
        f"{ENDINGS[mode]}"
    )
    return prompt, letter_meaning


if __name__ == "__main__":
    # Running this file on its own prints every version of one question,
    # so you can check the wording.
    for frame in ["gain", "loss"]:
        for mode in ["direct", "step_by_step"]:
            for order in ["sure_first", "risky_first"]:
                prompt, meaning = build_prompt("health", frame, mode, order)
                print(f"===== health | {frame} | {mode} | {order} | {meaning} =====")
                print(prompt)
                print()
