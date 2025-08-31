import cards.start_card
import cards.game_card
import cards.flow_manage_card

class AppController:
    def __init__(self, main_window):
        self.win = main_window
        self.current_card = None

    def start(self):
        self.show_start_card()

    def show_start_card(self):
        """显示初始的开始界面"""
        print("控制器：切换到 StartCard")
        start_ui = cards.start_card.DarkFramelessWindow()

        start_ui.on_start_game_clicked.connect(self.show_game_card)
        start_ui.on_manager_flow_clicked.connect(self.show_flow_manager_card)

        self._set_current_card(start_ui)

    def show_game_card(self):
        """显示游戏界面"""
        print("控制器：切换到 GameCard")
        game_ui = cards.game_card.GameCard()
        game_ui.return_to_menu_requested.connect(self.show_start_card)

        self._set_current_card(game_ui)

    def show_flow_manager_card(self):
        print("控制器：切换到 FlowManagerCard")
        flow_manager_ui = cards.flow_manage_card.FlowManagerCard()

        # flow_manager_card的返回信号也连接到显示主菜单的槽
        flow_manager_ui.return_to_menu_requested.connect(self.show_start_card)

        self._set_current_card(flow_manager_ui)

    def _set_current_card(self, card_widget):
        self.win.clear_cards()  # 清除旧卡片
        self.current_card = card_widget
        self.win.add_card(self.current_card)