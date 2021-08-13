import requests


class REST:
    """Allows to send REST API requests to Interactive Brokers Client Portal Web API.

    :param url: Gateway session link, defaults to "https://localhost:5000"
    :type url: str, optional
    :param ssl: Usage of SSL certificate, defaults to False
    :type ssl: bool, optional
    """

    def __init__(self, url="https://localhost:5000", ssl=False) -> None:
        """Create a new instance to interact with REST API

        :param url: Gateway session link, defaults to "https://localhost:5000"
        :type url: str, optional
        :param ssl: Usage of SSL certificate, defaults to False
        :type ssl: bool, optional
        """
        self.url = url + "/v1/api/"
        self.ssl = ssl
        self.id = self.get_accounts()[0]["accountId"]

    def get_accounts(self) -> list:
        """Returns account info

        :return: list of account info
        :rtype: list
        """
        response = requests.get(self.url + "portfolio/accounts", verify=self.ssl)
        return response.json()

    def switch_account(self, accountId: str) -> dict:
        """Switch selected account to the input account

        :param accountId: account ID of the desired account
        :type accountId: str
        :return: Response from the server
        :rtype: dict
        """
        response = requests.post(
            self.url + "iserver/account", json={"acctId": accountId}, verify=self.ssl
        )
        self.id = accountId
        return response.json()

    def get_cash(self) -> float:
        """Returns cash balance of the selected account

        :return: cash balance
        :rtype: float
        """
        response = requests.get(
            self.url + "portfolio/" + self.id + "/ledger",
            verify=self.ssl,
        )
        return response.json()["USD"]["cashbalance"]

    def get_netvalue(self) -> float:
        """Returns net value of the selected account

        :return: Net value in USD
        :rtype: float
        """
        response = requests.get(
            self.url + "portfolio/" + self.id + "/ledger",
            verify=self.ssl,
        )
        return response.json()["USD"]["netliquidationvalue"]

    def get_conid(self, symbol: str) -> int:
        """Returns contract id of the given instrument

        :param symbol: Symbol of the instrument
        :type symbol: str
        :return: contract id
        :rtype: int
        """
        query = {"symbols": symbol}
        response = requests.get(
            self.url + "trsrv/stocks", params=query, verify=self.ssl
        )
        dic = response.json()
        return dic[symbol][0]["contracts"][0]["conid"]

    def get_portfolio(self) -> dict:
        """Returns portfolio of the selected account

        :return: Portfolio
        :rtype: dict
        """
        response = requests.get(
            self.url + "portfolio/" + self.id + "/positions/0",
            verify=self.ssl,
        )
        dic = {}
        for item in response.json():
            dic.update({item["contractDesc"]: item["position"]})
        dic.update({"USD": self.get_cash()})  # Cash balance
        return dic

    def reply_yes(self, id: str) -> dict:
        """
        Replies yes to a single message generated while submitting or modifying orders.

        :param id: message ID
        :type id: str
        :return: Returned message
        :rtype: dict
        """

        answer = {"confirmed": True}
        response = requests.post(
            self.url + "iserver/reply/" + id,
            json=answer,
            verify=self.ssl,
        )
        return response.json()[0]

    def _reply_all_yes(self, response, reply_yes_to_all: bool) -> dict:
        """
        Replies yes to consecutive messages generated while submitting or modifying orders.
        """
        dic = response.json()[0]
        if reply_yes_to_all:
            while "order_id" not in dic.keys():
                print("Answering yes to ...")
                print(dic["message"])
                dic = self.reply_yes(dic["id"])
        return dic

    def submit_orders(self, list_of_orders: list, reply_yes=True) -> dict:
        """Submit a list of orders

        :param list_of_orders: List of order dictionaries. For each order dictionary, see `here <https://www.interactivebrokers.com/api/doc.html#tag/Order/paths/~1iserver~1account~1{accountId}~1orders/post>`_ for more details.
        :type list_of_orders: list
        :param reply_yes: Replies yes to returning messages or not, defaults to True
        :type reply_yes: bool, optional
        :return: Response to the order request
        :rtype: dict
        """
        response = requests.post(
            self.url + "iserver/account/" + self.id + "/orders",
            json={"orders": list_of_orders},
            verify=self.ssl,
        )
        return self._reply_all_yes(response, reply_yes)

    def get_order(self, orderId: str) -> dict:
        """Returns details of the order

        :param orderId: Order ID of the submitted order
        :type orderId: str
        :return: Details of the order
        :rtype: dict
        """
        response = requests.get(
            self.url + "iserver/account/order/status/" + str(orderId), verify=self.ssl
        )
        return response.json()

    def get_live_orders(self, filters=[]) -> dict:
        """Returns list of live orders

        :param filters: Filters for the returning response. Available items -- "inactive" "pending_submit" "pre_submitted" "submitted" "filled" "pending_cancel" "cancelled" "warn_state" "sort_by_time", defaults to []
        :type filters: list, optional
        :return: list of live orders
        :rtype: dict
        """
        response = requests.get(
            self.url + "iserver/account/orders",
            params={"filters": filters},
            verify=self.ssl,
        )
        return response.json()

    def cancel_order(self, orderId: str) -> dict:
        """Cancel the submitted order

        :param orderId: Order ID for the input order
        :type orderId: str
        :return: Response from the server
        :rtype: dict
        """
        response = requests.delete(
            self.url + "iserver/account/" + self.id + "/order/" + str(orderId),
            verify=self.ssl,
        )
        return response.json()

    def modify_order(
        self, orderId: str = None, order: dict = None, reply_yes=True
    ) -> dict:
        """Modify submitted order

        :param orderId: Order ID of the submitted order, defaults to None
        :type orderId: str
        :param order: Order dictionary, defaults to None
        :type order: dict
        :param reply_yes: Replies yes to the returning messages, defaults to True
        :type reply_yes: bool, optional
        :return: Response from the server
        :rtype: dict
        """
        assert (
            orderId != None and order != None
        ), "Input parameters (orderId or order) are missing"

        response = requests.post(
            self.url + "iserver/account/" + self.id + "/order/" + str(orderId),
            json=order,
            verify=self.ssl,
        )
        return self._reply_all_yes(response, reply_yes)

    def ping_server(self) -> dict:
        """Tickle server for maintaining connection

        :return: Response from the server
        :rtype: dict
        """
        response = requests.post(self.url + "tickle", verify=self.ssl)
        return response.json()

    def get_auth_status(self) -> dict:
        """Returns authentication status

        :return: Status dictionary
        :rtype: dict
        """
        response = requests.post(self.url + "iserver/auth/status", verify=self.ssl)
        return response.json()

    def re_authenticate(self) -> None:
        """Attempts to re-authenticate when authentication is lost
        """
        response = requests.post(self.url + "iserver/reauthenticate", verify=self.ssl)
        print("Reauthenticating ...")

    def log_out(self) -> None:
        """Log out from the gateway session
        """
        response = requests.post(self.url + "logout", verify=self.ssl)

    def get_bars(self, symbol: str, period="1w", bar="1d", outsideRth=False) -> dict:
        """Returns market history for the given instrument

        :param symbol: Symbol of the instrument
        :type symbol: str
        :param period: Period for the history, available time period-- {1-30}min, {1-8}h, {1-1000}d, {1-792}w, {1-182}m, {1-15}y, defaults to "1w"
        :type period: str, optional
        :param bar: Granularity of the history, possible value-- 1min, 2min, 3min, 5min, 10min, 15min, 30min, 1h, 2h, 3h, 4h, 8h, 1d, 1w, 1m, defaults to "1d"
        :type bar: str, optional
        :param outsideRth: For contracts that support it, will determine if historical data includes outside of regular trading hours., defaults to False
        :type outsideRth: bool, optional
        :return: Response from the server
        :rtype: dict
        """
        query = {
            "conid": self.get_conid(symbol),
            "period": period,
            "bar": bar,
            "outsideRth": outsideRth,
        }
        response = requests.get(
            self.url + "iserver/marketdata/history", params=query, verify=self.ssl
        )
        return response.json()


if __name__ == "__main__":

    api = REST()

    # print(api.reply_yes("a37bcc93-736b-441b-88a3-ee291d5dbcbd"))
    orders = [
        {
            "conid": api.get_conid("AAPL"),
            "orderType": "MKT",
            "side": "BUY",
            "quantity": 7,
            "tif": "GTC",
        }
    ]

    # print(api.submit_order(orders))
    # print(api.modify_order(1258176643, orders[0]))
    # print(api.get_order(1258176642))
    # print(api.get_portfolio())
    # print(api.re_authenticate())
    # print(api.get_auth_status())
    print(api.get_live_orders())
    # print(api.get_bars("TSLA"))
    # print(api.get_conid("AAPL"))
    # print(api.cancel_order(2027388848))
