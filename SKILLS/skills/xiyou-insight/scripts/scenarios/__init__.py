from .ad_monitoring import AdMonitoringScenario
from .traffic_gap import TrafficGapScenario
from .competitor_analysis import CompetitorAnalysisScenario
from .new_product import NewProductScenario
from .ad_budget import AdBudgetScenario
from .keyword_database import KeywordDatabaseScenario


SCENARIOS = {
    'ad_monitoring': AdMonitoringScenario,
    'traffic_gap': TrafficGapScenario,
    'competitor_analysis': CompetitorAnalysisScenario,
    'new_product': NewProductScenario,
    'ad_budget': AdBudgetScenario,
    'keyword_database': KeywordDatabaseScenario
}


def get_scenario(scenario_name: str):
    scenario_class = SCENARIOS.get(scenario_name)
    if not scenario_class:
        raise ValueError(f"Unknown scenario: {scenario_name}. Available scenarios: {list(SCENARIOS.keys())}")
    return scenario_class


def list_scenarios():
    return SCENARIOS.keys()
