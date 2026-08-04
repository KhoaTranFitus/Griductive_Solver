<!-- docs/architecture.md -->
GriductiveSolver/
│
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── assets/
│ ├── characters/
│ └── icons/
│
├── data/
│ ├── characters.json
│ └── levels/
│ └── level_01.json
│
├── core/
│ ├── init.py
│ ├── enums.py
│ ├── models.py
│ └── exceptions.py
│
├── game/
│ ├── init.py
│ ├── level_loader.py
│ ├── level_validator.py
│ ├── game_state.py
│ ├── public_state.py
│ └── game_engine.py
│
├── logic/
│ ├── init.py
│ ├── region_resolver.py
│ ├── semantic_evaluator.py
│ ├── variable_map.py
│ ├── cnf_encoder.py
│ ├── dpll.py
│ ├── entailment.py
│ └── deductive_agent.py
│
├── gui/
│ ├── init.py
│ ├── app.py
│ ├── game_screen.py
│ └── components.py
│
├── tests/
│ ├── test_loader.py
│ ├── test_regions.py
│ ├── test_encoder.py
│ ├── test_dpll.py
│ ├── test_entailment.py
│ └── test_engine.py
│
└── docs/
├── architecture.md
├── data_format.md
└── task_assignment.md