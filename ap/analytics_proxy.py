# ap/analytics_proxy.py
from typing import List
from .domain_models import (
    AnalyticsAvailable,
    AnalyticDef,
    StudentAnalytics,
    AnalyticValue,
    AnalyticsQuery,
)


class AnalyticsPersistenceProxy:
    """
    Proxy: encapsula o acesso à "persistência".
    Nesta versão, usamos MOCK em memória em vez de BD real.
    """

    def __init__(self) -> None:
        # MOCK de dados de analytics por activityID
        # Aqui você pode alterar os valores conforme simulação.
        self._mock_students_by_activity = {
            "TESTE123": [
                {
                    "inveniraStdID": "1001",
                    "events_count": 15,
                    "completed_words": 10,
                    "hints_used": 2,
                    "comment": "Aluno terminou a sopa com pequenas dificuldades."
                },
                {
                    "inveniraStdID": "1002",
                    "events_count": 8,
                    "completed_words": 5,
                    "hints_used": 0,
                    "comment": "Aluno abandonou a meio."
                },
            ],
            # Podemos acrescentar outras activities aqui...
        }

    def get_available_analytics(self) -> AnalyticsAvailable:
        """
        Simula o analytics_list_url da Inven!RA (lista de analytics disponíveis).
        """
        quant = [
            AnalyticDef(name="events_count",      type="integer"),
            AnalyticDef(name="completed_words",   type="integer"),
            AnalyticDef(name="hints_used",        type="integer"),
        ]
        qual = [
            AnalyticDef(name="comment",           type="text/plain"),
        ]
        return AnalyticsAvailable(qualAnalytics=qual, quantAnalytics=quant)

    def get_analytics_for_activity(self, query: AnalyticsQuery) -> List[StudentAnalytics]:
        """
        Simula o analytics_url: devolve analytics por estudante, em formato Inven!RA.
        O parâmetro query pode filtrar por um métrico específico ou "all".
        """
        raw_list = self._mock_students_by_activity.get(query.activity_id, [])
        result: List[StudentAnalytics] = []

        for row in raw_list:
            invenira_id = row.get("inveniraStdID")
            quant_values: List[AnalyticValue] = []
            qual_values: List[AnalyticValue] = []

            for key, value in row.items():
                if key == "inveniraStdID":
                    continue

                # métricas quantitativas (integers)
                if key in {"events_count", "completed_words", "hints_used"}:
                    if query.query not in ("all", key):
                        continue
                    quant_values.append(
                        AnalyticValue(
                            name=key,
                            type="integer",
                            value=value
                        )
                    )

                # métricas qualitativas (texto, URL, etc.)
                elif key == "comment":
                    if query.query not in ("all", key):
                        continue
                    qual_values.append(
                        AnalyticValue(
                            name="comment",
                            type="text/plain",
                            value=value
                        )
                    )

            result.append(
                StudentAnalytics(
                    inveniraStdID=invenira_id,
                    quantAnalytics=quant_values,
                    qualAnalytics=qual_values,
                )
            )

        return result
