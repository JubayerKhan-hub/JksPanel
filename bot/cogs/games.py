from __future__ import annotations

import random
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from ..utils.database import bump_game_stat, get_game_stats


class RPSView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=30)
        self.author_id = author_id
        self.result: Optional[str] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @discord.ui.button(label="Rock", style=discord.ButtonStyle.secondary)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._play(interaction, "rock")

    @discord.ui.button(label="Paper", style=discord.ButtonStyle.secondary)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._play(interaction, "paper")

    @discord.ui.button(label="Scissors", style=discord.ButtonStyle.secondary)
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._play(interaction, "scissors")

    async def _play(self, interaction: discord.Interaction, choice: str) -> None:
        options = ["rock", "paper", "scissors"]
        bot_choice = random.choice(options)
        outcome = self._judge(choice, bot_choice)
        self.result = outcome
        await interaction.response.edit_message(content=f"You: {choice} | Bot: {bot_choice} -> {outcome.upper()}!", view=None)
        self.stop()

    @staticmethod
    def _judge(player: str, bot: str) -> str:
        if player == bot:
            return "draw"
        wins = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
        return "win" if wins[player] == bot else "loss"


class TicTacToeButton(discord.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label=" ", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction) -> None:  # type: ignore[override]
        view: TicTacToeView = self.view  # type: ignore[assignment]
        if interaction.user.id != view.player_x and interaction.user.id != view.player_o:
            await interaction.response.send_message("You're not playing this game.", ephemeral=True)
            return
        if view.current_player != interaction.user.id:
            await interaction.response.send_message("It's not your turn.", ephemeral=True)
            return
        if view.board[self.y][self.x] != 0:
            await interaction.response.send_message("That spot is taken.", ephemeral=True)
            return
        mark = 1 if view.current_player == view.player_x else 2
        view.board[self.y][self.x] = mark
        self.label = "X" if mark == 1 else "O"
        self.disabled = True
        winner = view.check_winner()
        if winner:
            for child in view.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
            await interaction.response.edit_message(content=f"Winner: {'X' if winner == 1 else 'O'}!", view=view)
            view.stop()
        elif view.is_board_full():
            await interaction.response.edit_message(content="It's a draw!", view=view)
            view.stop()
        else:
            view.current_player = view.player_o if view.current_player == view.player_x else view.player_x
            await interaction.response.edit_message(view=view)


class TicTacToeView(discord.ui.View):
    def __init__(self, player_x: int, player_o: int):
        super().__init__(timeout=120)
        self.player_x = player_x
        self.player_o = player_o
        self.current_player = player_x
        self.board = [[0] * 3 for _ in range(3)]
        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_winner(self) -> int | None:
        lines = []
        b = self.board
        lines.extend(b)
        lines.extend([[b[0][i], b[1][i], b[2][i]] for i in range(3)])
        lines.append([b[0][0], b[1][1], b[2][2]])
        lines.append([b[0][2], b[1][1], b[2][0]])
        for line in lines:
            if line == [1, 1, 1]:
                return 1
            if line == [2, 2, 2]:
                return 2
        return None

    def is_board_full(self) -> bool:
        return all(cell != 0 for row in self.board for cell in row)


class Games(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rps", description="Play rock-paper-scissors")
    async def rps(self, interaction: discord.Interaction) -> None:
        view = RPSView(author_id=interaction.user.id)
        await interaction.response.send_message("Choose your move:", view=view)
        await view.wait()
        if view.result:
            if view.result == "win":
                bump_game_stat(interaction.user.id, "rps", "win")
            elif view.result == "loss":
                bump_game_stat(interaction.user.id, "rps", "loss")
            else:
                bump_game_stat(interaction.user.id, "rps", "draw")

    @app_commands.command(name="rpsstats", description="Your RPS stats")
    async def rpsstats(self, interaction: discord.Interaction) -> None:
        w, l, d = get_game_stats(interaction.user.id, "rps")
        await interaction.response.send_message(f"Wins: {w} | Losses: {l} | Draws: {d}")

    @app_commands.command(name="tictactoe", description="Play TicTacToe vs another player")
    async def tictactoe(self, interaction: discord.Interaction, opponent: discord.Member) -> None:
        if opponent.id == interaction.user.id:
            await interaction.response.send_message("You cannot play against yourself.", ephemeral=True)
            return
        view = TicTacToeView(player_x=interaction.user.id, player_o=opponent.id)
        await interaction.response.send_message(
            f"TicTacToe: X = {interaction.user.mention}, O = {opponent.mention}. {interaction.user.mention} goes first.",
            view=view,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Games(bot))