"""Основной модуль для расчета показателей экономической эффективности
проекта строительства жилого комплекса (NPV, IRR, период окупаемости).
Исходные данные для расчета импортируются из модуля пользовательского интерфейса.
Расчет денежного потока производится в поквартальной динамике.
График продаж квартир рассчитывается автоматически с учетом масштаба проекта,
ценового класса и типичного распределения спроса по этапам строительства.
Допущения, заложенные в расчет:
1. Темпы продаж квартир зависят от масштаба жилого комплекса и от уровня цен:
   - Жилой комплекс массового ценового сегмента может быть продан за 2,5-3,5 года.
   - Жилой комплекс верхней ценовой категории может быть продан за 3-4 года.
2. После начала продаж спрос на квартиры постепенно увеличивается и достигает
   пика примерно к концу первой трети строительного цикла. Затем спрос постепенно
   снижается. В большинстве проектов после ввода в эксплуатацию остается
   некоторый объем нераспроданных квартир.
3. Стоимость кв. метра и темпы роста зависят от этапа строительства:
   - Наибольший прирост цен наблюдается к завершающему этапу строительства и вводу в эксплуатацию.
   - Цены на квартиры в сданных домах продолжают дорожать менее значительными темпами.
5. Крупные проекты реализуются очередями - каждая следующая очередь выводится в продажу,
   когда в предыдущей очереди распродан основной объем квартир.
   Очереди могут рассматриваться как самостоятельные проекты.
6. Поступления от продаж квартир на этапе строительства не могут использоваться застройщиком
   до сдачи дома в эксплуатацию и хранятся на эскроу-счетах в банке.
7. Отрицательный денежный поток на этапе строительства финансируется из кредитной линии
   или из собственных средств застройщика. В данном расчете выплаты процентов
   по банковскому кредиту не учитываются.
"""

import gui  # Модуль пользовательского интерфейса

import pandas as pd
import numpy as np
from scipy.stats import gamma
import matplotlib.pyplot as plt

plt.style.use('fivethirtyeight')
plt.rcParams['figure.figsize'] = 12, 7

# Исходные параметры, заданные пользователем:
parameters = gui.parameters

# Допущения для планирования темпов продаж:
assumptions = {
    'mass_market': {
        'price_range': [80_000, 120_000],
        'sales_period': [10, 14],  # Период реализации в кварталах
        'max_phase_size': 55_000  # Максимальная площадь квартир в одной очереди
    },
    'upper_class': {
        'price_range': [120_000, 150_000],
        'sales_period': [12, 16],
        'max_phase_size': 40_000
    }
}


class Estimation:

    """Класс для расчета показателей экономической эффективности
    проекта строительства жилого комплекса."""

    def __init__(self, pars: dict):
        self.parameters = pars
        self.estimate_project()

    def estimate_project(self):
        """Главная функция класса, агрегирует вызовы всех других функций,
        сохраняет таблицу с расчетами в файл формата Excel."""
        self.get_quarterly_rates()
        self.split_to_phases()
        self.phase_sales_period()
        self.sales_sqm()
        self.sales_rubles()
        self.get_revenue()
        self.get_expenses()
        self.get_metrics()
        self.save_results()

    def get_quarterly_rates(self):
        """Функция производит расчет квартальных ставок."""
        for rate in ('inflation', 'discount_rate'):
            self.parameters[f'{rate}_quarterly'] = self.parameters[f'{rate}_annual'] ** (1 / 4)

    def split_to_phases(self):
        """Функция определяет количество очередей строительства
        и объем одной очереди в зависимости от ценового класса проекта."""
        self.parameters['price_segment'] = 'mass_market' if parameters['start_price'] < 120_000 else 'upper_class'
        phase_limit = assumptions[self.parameters['price_segment']]['max_phase_size']
        self.parameters['n_phases'] = int(self.parameters['apartment_area'] // phase_limit) + 1
        self.parameters['phase_floor_area'] = self.parameters['floor_area'] / self.parameters['n_phases']
        self.parameters['phase_apartment_area'] = self.parameters['apartment_area'] / self.parameters['n_phases']
        print(f'Количество очередей строительства: {self.parameters["n_phases"]}')

    def phase_sales_period(self):
        """Функция определяет период реализации квартир в одной очереди проекта."""
        min_price, max_price = assumptions[self.parameters['price_segment']]['price_range']
        min_quarters, max_quarters = assumptions[self.parameters['price_segment']]['sales_period']
        # Датафрейм с ценами на старте продаж и соответствующим периодом реализации:
        sales = pd.DataFrame({'price': [price for price in range(min_price, max_price + 1, 1_000)]})
        sales['n_quarters'] = np.nan
        sales.loc[sales['price'] == min_price, 'n_quarters'] = min_quarters
        sales.loc[sales['price'] == max_price, 'n_quarters'] = max_quarters
        # Все значения между минимумом и максимумом интерполируем линейно:
        sales['n_quarters'] = sales['n_quarters'].interpolate()
        self.sales_period = int(np.ceil(sales.loc[sales['price'] == self.parameters['start_price'],
                                             'n_quarters'].values[0]))
        print(f'Период продаж одной очереди: {self.sales_period} кварталов')

    def sales_sqm(self):
        """Функция вычисляет продаваемую площадь квартир по кварталам в рамках одной очереди."""
        # Гамма-распределение с пиком на границе 1/3 строительного цикла:
        peak_quarter = self.parameters['construction_period'] // 3
        x = np.linspace(gamma.ppf(0.01, peak_quarter),
                        gamma.ppf(0.99, peak_quarter), self.sales_period)
        y = gamma.pdf(x, peak_quarter)
        y_normalized = y / np.sum(y)  # Продажи по кварталам в долях от 1
        # Датафрейм, где номеру квартала соответствует продаваемая площадь:
        self.sales_distribution = pd.DataFrame({'quarter': [q for q in range(1, self.sales_period + 1)]})
        self.sales_distribution['sales_sqm'] = self.parameters['apartment_area'] * y_normalized
        self.plot_sales()

    def plot_sales(self):
        """Функция формирует и сохраняет в файл график продаж одной очереди."""
        plt.bar(self.sales_distribution['quarter'], self.sales_distribution['sales_sqm'])
        plt.xlabel('Кварталы')
        plt.ylabel('Продаваемая площадь, кв. м')
        plt.title('График продаж по кварталам')
        price = self.parameters["start_price"]
        phase_size = self.parameters["phase_apartment_area"]
        plt.figtext(0.5, 0.8,
                    f'Цена на старте продаж: {price} руб./кв. м\nОбъем 1 очереди: {phase_size} кв. м',
                    fontweight="bold")
        plt.tight_layout()
        plt.savefig('sales.png', dpi=300)
        plt.show()

    def price_indexes(self):
        """Функция оценивает индексы роста цен по отношению к цене на старте продаж
        для всего периода реализации квартир в рамках одной очереди проекта."""
        self.cash_flow = pd.DataFrame({
            'quarter': [q for q in range(1, self.parameters['construction_period'] + 1)],
            'status': 'construction'})
        # Индексы роста цен по отношению к цене на старте:
        quarterly_increase = self.parameters['completion_premium'] ** (1 / self.parameters['construction_period'])
        self.cash_flow['price_index'] = quarterly_increase ** self.cash_flow['quarter']
        # После сдачи в эксплуатацию цены увеличиваются в пределах инфляции:
        if self.parameters['construction_period'] < len(self.sales_distribution):
            after_completion = pd.DataFrame({
                'quarter': [q for q in range(self.cash_flow['quarter'].max() + 1,
                                             self.sales_distribution['quarter'].max() + 1)],
                'status': 'completed'})
            # Индексы прироста цен к максимальной цене в сданном доме:
            after_completion['price_index'] = [
                self.cash_flow['price_index'].max() * self.parameters['inflation_quarterly']
                ** q for q in range(1, len(after_completion) + 1)]
            self.cash_flow = self.cash_flow.append(after_completion[['quarter', 'price_index', 'status']],
                                                   ignore_index=True)

    def sales_rubles(self):
        """Функция подсчитывает денежные поступления от реализации квартир."""
        self.price_indexes()  # Индексы роста цен по кварталам
        self.cash_flow['price'] = self.cash_flow['price_index'] * self.parameters['start_price']
        self.cash_flow['sales_sq_m'] = self.sales_distribution['sales_sqm']
        self.cash_flow['sales_rub'] = self.cash_flow['price'] * self.cash_flow['sales_sq_m']

    def get_revenue(self):
        """Функция подсчитывает выручку при условии, что средства от реализации квартир
        становятся доступны в первый квартал после ввода дома в эксплуатацию."""
        self.cash_flow['revenue'] = 0
        indexes_completed = self.cash_flow.loc[self.cash_flow['status'] == 'completed'].index
        self.cash_flow.loc[indexes_completed, 'revenue'] = self.cash_flow.loc[indexes_completed, 'sales_rub']
        quarter_after_completion = indexes_completed.min()
        sales_before_completion = self.cash_flow.loc[:quarter_after_completion - 1, 'sales_rub'].sum()
        self.cash_flow.loc[quarter_after_completion, 'revenue'] += sales_before_completion

    def get_expenses(self):
        """Функция подсчитывает затраты на реализацию проекта."""
        # Затраты на строительство распределены равномерно до ввода в эксплуатацию:
        self.cash_flow['construction_costs'] = self.parameters['construction_costs'] * \
                            self.parameters['floor_area'] / self.parameters['construction_period']
        # Затраты на продвижение, рекламу, агентское вознаграждение - процентом от объема продаж:
        self.cash_flow['promotion'] = self.cash_flow['sales_rub'] * 0.06
        self.cash_flow['expenses'] = self.cash_flow['construction_costs'] + self.cash_flow['promotion']

    def get_metrics(self):
        """Функция вычисляет NPV, период окупаемости
        и внутреннюю норму доходности проекта."""
        # Денежный поток проекта:
        self.cash_flow['CF'] = self.cash_flow['revenue'] - self.cash_flow['expenses']
        # Дисконтированный денежный поток проекта:
        self.cash_flow['discount_coef'] = self.parameters['discount_rate_quarterly'] ** self.cash_flow['quarter']
        self.cash_flow['DCF'] = self.cash_flow['CF'] / self.cash_flow['discount_coef']
        for par in ('CF', 'DCF'):
            self.cash_flow[f'{par}_cumsum'] = self.cash_flow[par].cumsum()
        self.parameters['NPV'] = int(self.cash_flow['DCF'].sum())  # NPV дисконтированного денежного потока
        self.parameters['PBP'] = self.cash_flow[self.cash_flow['CF_cumsum'] > 0]['quarter'].min()
        self.parameters['DPBP'] = self.cash_flow[self.cash_flow['DCF_cumsum'] > 0]['quarter'].min()
        self.parameters['IRR'] = np.round(np.irr(self.cash_flow['DCF']), 3)
        results = f'NPV = {self.parameters["NPV"]}\nPBP = {self.parameters["PBP"]} кварталов\n' \
                  f'DPBP = {self.parameters["DPBP"]} кварталов\nIRR = {self.parameters["IRR"]}'
        self.plot_CF(results)

    def plot_CF(self, metrics: str):
        """Функция формирует и сохраняет в файл график с динамикой
        денежного потока и показателями экономической эффективности проекта."""
        plt.bar(self.cash_flow['quarter'], self.cash_flow['CF_cumsum'], label='Накопленный денежный поток')
        plt.bar(self.cash_flow['quarter'], self.cash_flow['DCF_cumsum'], label='Накопленный дисконтированный поток')
        plt.figtext(0.1, 0.2, metrics, fontweight="bold")
        plt.legend()
        plt.xlabel('Кварталы')
        plt.ylabel('Руб.')
        plt.title('Показатели эффективности проекта')
        plt.tight_layout()
        plt.savefig('cash_flow.png', dpi=300)
        plt.show()

    def save_results(self):
        """Функция сохраняет результаты расчетов в файл Excel."""
        input_pars = pd.DataFrame(self.parameters, index=[0])
        with pd.ExcelWriter('Estimation.xlsx') as writer:
            input_pars.T.to_excel(writer, sheet_name='inputs', header=False)
            self.cash_flow.T.to_excel(writer, sheet_name='cash_flow', header=False)


result = Estimation(parameters)
