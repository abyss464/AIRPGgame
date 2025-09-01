import cards.start_card
import cards.game_card
import cards.flow_manage_card


class AppController:
    def __init__(self, main_window):
        self.win = main_window

        # 1. 一次性创建所有卡片的实例
        print("控制器：正在初始化并创建所有卡片实例...")
        self.start_card = cards.start_card.DarkFramelessWindow()
        self.game_card = cards.game_card.GameCard()
        self.flow_manager_card = cards.flow_manage_card.HierarchicalFlowManagerUI()

        # 将所有卡片实例存入一个列表中，方便管理（可选，但推荐）
        self.all_cards = [self.start_card, self.game_card, self.flow_manager_card]

        # 2. 一次性连接所有信号和槽
        self._connect_signals()

    def _connect_signals(self):
        """将所有信号连接的逻辑集中在此处，只在初始化时调用一次"""
        print("控制器：正在连接所有信号...")
        # StartCard 的信号
        self.start_card.on_start_game_clicked.connect(self.show_game_card)
        self.start_card.on_manager_flow_clicked.connect(self.show_flow_manager_card)
        self.start_card.send_log.connect(self.on_log_request)

        # GameCard 的信号
        self.game_card.return_to_menu_requested.connect(self.show_start_card)
        self.game_card.send_log.connect(self.on_log_request)

        # FlowManagerCard 的信号
        self.flow_manager_card.return_to_menu_requested.connect(self.show_start_card)
        self.flow_manager_card.send_log.connect(self.on_log_request)

    def on_log_request(self, text: str):
        self.win.append_output(text)

    def start(self):
        """应用程序的入口点"""
        self.show_start_card()

    def show_start_card(self):
        """显示初始的开始界面"""
        print("控制器：切换到 StartCard")
        # 直接使用预先创建的实例
        self._switch_to_card(self.start_card)

    def show_game_card(self):
        """显示游戏界面"""
        print("控制器：切换到 GameCard")
        # 直接使用预先创建的实例
        self._switch_to_card(self.game_card)

    def show_flow_manager_card(self):
        """显示流程管理界面"""
        print("控制器：切换到 FlowManagerCard")
        # 直接使用预先创建的实例
        self._switch_to_card(self.flow_manager_card)

    def _switch_to_card(self, card_widget):
        """
        切换当前显示的卡片。
        这个方法重用了你原有的布局管理逻辑。
        """
        self.win.clear_cards()  # 假设这个方法会从布局中移除所有旧卡片
        self.win.add_card(card_widget)  # 假设这个方法会将新卡片添加到布局中并显示
        # 注意: card_widget.show() 可能需要显式调用，但这取决于 self.win.add_card 的实现方式
        # 大多数情况下，将 widget 添加到可见的布局中会自动使其可见。

