# Same Facts, Different Frames

<!-- OUTLINE ONLY. Ranveer: replace every bullet with your own sentences. -->

## The question
- One sentence: do people and AI models choose differently when the same outcome is described as a gain vs a loss?
- The classic result: Tversky & Kahneman (1981), the "Asian disease" problem.

## What I did
### Students
- 5 scenarios (health, money, exam marks, jobs, crops); in each, the sure and risky options have the same expected value.
- Two Google Forms, one per frame; each student saw only one frame.
- First 15 valid responses per form, by time submitted (a fixed rule, decided before looking at results).

### AI models
- 6 models: a flagship and a small model from Anthropic, OpenAI and Google (exact model names and dates here).
- Same 5 questions, word for word, asked 30 times per frame, either answering directly or thinking step by step.
- Option order swapped on half the runs, so a model can't just favour "A".
- Built-in reasoning switched off where the API allows (see `results/tables/model_call_summary.csv`).

## Results
- Headline chart: `results/figures/headline.png`
- One or two sentences on the students' result.
- One or two sentences on the models: which showed the effect, which didn't.
- Did thinking step by step shrink it? (`results/figures/step_by_step.png`)

## Limitations
- 15 students per frame, one school.
- Hypothetical choices, not real stakes.
- Models change over time; results are for the model versions and dates listed above.

## How to run it
```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # then add your API keys
python src/analyse_students.py
python src/run_models.py
python src/score.py
python src/analyse_models.py
python src/make_charts.py
```

## Files
| File | What it does |
|---|---|
| `src/items.py` | The 5 questions in both frames, and how a prompt is built |
| `src/run_models.py` | Sends every prompt to every model and logs every reply |
| `src/score.py` | Reads each reply's answer and turns it into sure / risky |
| `src/analyse_students.py` | Student statistics |
| `src/analyse_models.py` | Model statistics |
| `src/make_charts.py` | The three charts |
