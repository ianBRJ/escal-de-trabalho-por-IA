from __future__ import annotations

try:
    import tkinter as tk
    from tkinter import messagebox, scrolledtext, ttk
except ImportError:  # pragma: no cover - fallback para ambientes sem Tkinter
    tk = None
    messagebox = None
    scrolledtext = None
    ttk = None

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Set


@dataclass
class Funcionario:
    nome: str
    cargo: str
    prioridade: int = 1
    grupo: Optional[str] = None
    escala_tipo: str = "dias_trabalho"
    dias_trabalho_alvo: int = 5
    dias_folga_alvo: int = 2
    bloqueios: Set[str] = field(default_factory=set)


class GerenciadorEscala:
    def __init__(self) -> None:
        self.funcionarios: List[Funcionario] = []
        self.escala_tipo_global: str = "dias_trabalho"
        self.dias_importantes: Set[str] = set()
        self.escala_gerada: Dict[str, Dict[str, List[str]]] = {}

    def adicionar_funcionario(
        self,
        nome: str,
        cargo: str,
        prioridade: int = 1,
        grupo: Optional[str] = None,
        escala_tipo: str = "dias_trabalho",
        dias_trabalho_alvo: int = 5,
        dias_folga_alvo: int = 2,
    ) -> None:
        if not nome.strip():
            raise ValueError("Nome do funcionário não pode ficar vazio.")

        self.funcionarios.append(
            Funcionario(
                nome=nome.strip(),
                cargo=cargo.strip(),
                prioridade=prioridade,
                grupo=grupo.strip() if grupo else None,
                escala_tipo=escala_tipo,
                dias_trabalho_alvo=dias_trabalho_alvo,
                dias_folga_alvo=dias_folga_alvo,
            )
        )

    def definir_tipo_escala_global(self, escala_tipo: str) -> None:
        if escala_tipo not in {"dias_trabalho", "dias_folga"}:
            raise ValueError("Use 'dias_trabalho' ou 'dias_folga'.")
        self.escala_tipo_global = escala_tipo

    def definir_grupo(self, nome_funcionario: str, grupo: str) -> None:
        for funcionario in self.funcionarios:
            if funcionario.nome.lower() == nome_funcionario.lower():
                funcionario.grupo = grupo.strip() if grupo.strip() else None
                return
        raise ValueError(f"Funcionário '{nome_funcionario}' não encontrado.")

    def bloquear_dia(self, nome_funcionario: str, data: str) -> None:
        for funcionario in self.funcionarios:
            if funcionario.nome.lower() == nome_funcionario.lower():
                funcionario.bloqueios.add(data)
                return
        raise ValueError(f"Funcionário '{nome_funcionario}' não encontrado.")

    def marcar_dia_importante(self, data: str) -> None:
        self.dias_importantes.add(data)

    def _peso_dia(self, dia: date) -> float:
        if dia.weekday() == 5:
            return 1.5
        if dia.weekday() == 6:
            return 2.5
        return 1.0

    def _status_do_dia(self, func: Funcionario, dia: date, contador: Dict[str, int]) -> str:
        dia_str = dia.isoformat()

        if dia_str in func.bloqueios:
            return "folga"

        if dia_str in self.dias_importantes:
            if contador.get(func.nome, 0) < func.dias_trabalho_alvo:
                return "trabalho"
            return "folga"

        if dia.weekday() in (5, 6):
            if contador.get(func.nome, 0) < func.dias_trabalho_alvo:
                return "trabalho"
            return "folga"

        if self.escala_tipo_global == "dias_folga":
            if contador.get(func.nome, 0) >= func.dias_folga_alvo:
                return "trabalho"
            return "folga"

        if contador.get(func.nome, 0) < func.dias_trabalho_alvo:
            return "trabalho"
        return "folga"

    def gerar_escala(self, data_inicio: str, data_fim: str) -> Dict[str, Dict[str, List[str]]]:
        inicio = self._parse_data(data_inicio)
        fim = self._parse_data(data_fim)

        if fim < inicio:
            raise ValueError("Data final não pode ser anterior à data inicial.")

        contador = {func.nome: 0 for func in self.funcionarios}
        self.escala_gerada = {}

        dia_atual = inicio
        while dia_atual <= fim:
            dia_str = dia_atual.isoformat()
            self.escala_gerada[dia_str] = {"trabalho": [], "folga": []}

            for func in self.funcionarios:
                if dia_str in func.bloqueios:
                    self.escala_gerada[dia_str]["folga"].append(func.nome)
                    continue

                if func.grupo:
                    grupo = func.grupo
                    membros = [f for f in self.funcionarios if f.grupo == grupo and f.nome != func.nome]
                    if len(membros) >= 1:
                        todos_disponiveis = all(dia_str not in f.bloqueios for f in membros)
                        if todos_disponiveis and self._peso_dia(dia_atual) >= 1.5:
                            self.escala_gerada[dia_str]["trabalho"].append(func.nome)
                            contador[func.nome] += 1
                            continue

                status = self._status_do_dia(func, dia_atual, contador)
                if status == "trabalho":
                    self.escala_gerada[dia_str]["trabalho"].append(func.nome)
                    contador[func.nome] += 1
                else:
                    self.escala_gerada[dia_str]["folga"].append(func.nome)

            dia_atual += timedelta(days=1)

        return self.escala_gerada

    def listar_funcionarios(self) -> str:
        if not self.funcionarios:
            return "Nenhum funcionário cadastrado."

        linhas: List[str] = []
        for i, func in enumerate(self.funcionarios, start=1):
            grupo = func.grupo or "sem grupo"
            bloqueios = ", ".join(sorted(func.bloqueios)) if func.bloqueios else "nenhum"
            linhas.append(
                f"{i}. {func.nome} | Cargo: {func.cargo} | Prioridade: {func.prioridade} | "
                f"Grupo: {grupo} | Tipo: {func.escala_tipo} | Bloqueios: {bloqueios}"
            )
        return "\n".join(linhas)

    @staticmethod
    def _parse_data(data: str) -> date:
        try:
            return date.fromisoformat(data)
        except ValueError as exc:
            raise ValueError(f"Data inválida: {data}. Use o formato YYYY-MM-DD.") from exc


def carregar_exemplo(app: GerenciadorEscala) -> None:
    app.adicionar_funcionario(
        "Ana",
        "Supervisor",
        prioridade=1,
        grupo="Supervisor",
        escala_tipo="dias_trabalho",
        dias_trabalho_alvo=6,
        dias_folga_alvo=1,
    )
    app.adicionar_funcionario(
        "Bruno",
        "Supervisor",
        prioridade=1,
        grupo="Supervisor",
        escala_tipo="dias_trabalho",
        dias_trabalho_alvo=6,
        dias_folga_alvo=1,
    )
    app.adicionar_funcionario(
        "Carla",
        "Consultor",
        prioridade=1,
        grupo="Consultor",
        escala_tipo="dias_trabalho",
        dias_trabalho_alvo=6,
        dias_folga_alvo=1,
    )
    app.adicionar_funcionario(
        "Diego",
        "Consultor",
        prioridade=1,
        grupo="Consultor",
        escala_tipo="dias_trabalho",
        dias_trabalho_alvo=6,
        dias_folga_alvo=1,
    )

    app.definir_tipo_escala_global("dias_trabalho")
    app.bloquear_dia("Ana", "2026-10-08")
    app.bloquear_dia("Carla", "2026-10-10")
    app.marcar_dia_importante("2026-10-11")
    app.marcar_dia_importante("2026-10-12")


def menu() -> None:
    app = GerenciadorEscala()
    carregar_exemplo(app)

    while True:
        print("\n=== MENU ===")
        print("1. Cadastrar funcionário")
        print("2. Definir tipo de escala global")
        print("3. Definir grupo para funcionário")
        print("4. Bloquear dia para funcionário")
        print("5. Marcar dia importante")
        print("6. Gerar escala")
        print("7. Ver funcionários")
        print("8. Ver escala gerada")
        print("9. Sair")

        try:
            opcao = input("Escolha uma opção: ").strip()
        except EOFError:
            print("\nPrograma encerrado.")
            break

        if opcao == "1":
            nome = input("Nome: ").strip()
            cargo = input("Cargo: ").strip()
            prioridade = int(input("Prioridade (1 = alta, 3 = baixa): ") or "1")
            grupo = input("Grupo (opcional): ").strip() or None
            escala_tipo = input("Tipo da escala [dias_trabalho/dias_folga]: ").strip() or "dias_trabalho"
            dias_trabalho_alvo = int(input("Dias de trabalho alvo: ") or "5")
            dias_folga_alvo = int(input("Dias de folga alvo: ") or "2")
            app.adicionar_funcionario(
                nome,
                cargo,
                prioridade=prioridade,
                grupo=grupo,
                escala_tipo=escala_tipo,
                dias_trabalho_alvo=dias_trabalho_alvo,
                dias_folga_alvo=dias_folga_alvo,
            )
            print("Funcionário cadastrado com sucesso.")

        elif opcao == "2":
            escala_tipo = input("Tipo de escala [dias_trabalho/dias_folga]: ").strip()
            app.definir_tipo_escala_global(escala_tipo)
            print(f"Tipo global definido: {escala_tipo}")

        elif opcao == "3":
            nome = input("Nome do funcionário: ").strip()
            grupo = input("Nome do grupo: ").strip()
            app.definir_grupo(nome, grupo)
            print(f"Funcionário {nome} vinculado ao grupo {grupo}.")

        elif opcao == "4":
            nome = input("Nome do funcionário: ").strip()
            data = input("Data para bloquear (YYYY-MM-DD): ").strip()
            app.bloquear_dia(nome, data)
            print(f"Dia {data} bloqueado para {nome}.")

        elif opcao == "5":
            data = input("Data importante (YYYY-MM-DD): ").strip()
            app.marcar_dia_importante(data)
            print(f"Dia {data} marcado como importante.")

        elif opcao == "6":
            inicio = input("Data inicial (YYYY-MM-DD): ").strip()
            fim = input("Data final (YYYY-MM-DD): ").strip()
            try:
                app.gerar_escala(inicio, fim)
                print("Escala gerada com sucesso.")
            except ValueError as exc:
                print(f"Erro ao gerar escala: {exc}")

        elif opcao == "7":
            print(app.listar_funcionarios())

        elif opcao == "8":
            if not app.escala_gerada:
                print("Ainda não há escala gerada. Use a opção 6 primeiro.")
            else:
                for dia, dados in app.escala_gerada.items():
                    print(f"\n{dia}:")
                    print(f"  Trabalho: {', '.join(dados['trabalho']) if dados['trabalho'] else 'Nenhum'}")
                    print(f"  Folga: {', '.join(dados['folga']) if dados['folga'] else 'Nenhum'}")

        elif opcao == "9":
            print("Programa encerrado.")
            break

        else:
            print("Opção inválida.")


if tk is not None:
    class EscalaApp(tk.Tk):
        def __init__(self) -> None:
            super().__init__()
            self.title("Gerenciador de Escala de Funcionários")
            self.geometry("1100x750")

            self.gerenciador = GerenciadorEscala()
            self.criar_widgets()
            carregar_exemplo(self.gerenciador)
            self.atualizar_lista_funcionarios()

        def criar_widgets(self) -> None:
            self.configure(bg="#f4f4f4")

            frame = ttk.Frame(self, padding=12)
            frame.pack(fill="both", expand=True)

            left = ttk.Frame(frame)
            left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

            right = ttk.Frame(frame)
            right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

            frame.columnconfigure(0, weight=3)
            frame.columnconfigure(1, weight=4)
            frame.rowconfigure(0, weight=1)

            ttk.Label(left, text="Cadastro de funcionário", font=("Arial", 12, "bold")).grid(
                row=0, column=0, columnspan=2, sticky="w", pady=(0, 10)
            )

            labels = [
                ("Nome", 1),
                ("Cargo", 2),
                ("Prioridade", 3),
                ("Grupo", 4),
                ("Tipo da escala", 5),
                ("Dias trabalho alvo", 6),
                ("Dias folga alvo", 7),
            ]

            self.entradas = {}
            for texto, linha in labels:
                ttk.Label(left, text=texto).grid(row=linha, column=0, sticky="w", padx=(0, 8), pady=4)
                entry = ttk.Entry(left, width=28)
                entry.grid(row=linha, column=1, sticky="ew", pady=4)
                self.entradas[texto] = entry

            self.entradas["Prioridade"].insert(0, "1")
            self.entradas["Tipo da escala"].insert(0, "dias_trabalho")
            self.entradas["Dias trabalho alvo"].insert(0, "5")
            self.entradas["Dias folga alvo"].insert(0, "2")

            ttk.Button(left, text="Adicionar funcionário", command=self.adicionar_funcionario_ui).grid(
                row=8, column=0, columnspan=2, sticky="ew", pady=(10, 4)
            )

            ttk.Separator(left, orient="horizontal").grid(row=9, column=0, columnspan=2, sticky="ew", pady=10)

            ttk.Label(left, text="Definições da escala").grid(row=10, column=0, columnspan=2, sticky="w")

            ttk.Label(left, text="Tipo global").grid(row=11, column=0, sticky="w", pady=4)
            self.tipo_global = ttk.Combobox(left, values=["dias_trabalho", "dias_folga"], width=25)
            self.tipo_global.grid(row=11, column=1, sticky="ew", pady=4)
            self.tipo_global.set("dias_trabalho")

            ttk.Button(left, text="Aplicar tipo global", command=self.aplicar_tipo_global).grid(
                row=12, column=0, columnspan=2, sticky="ew", pady=(6, 4)
            )

            ttk.Label(left, text="Bloquear dia para funcionário").grid(row=13, column=0, columnspan=2, sticky="w", pady=(10, 0))

            ttk.Label(left, text="Funcionário").grid(row=14, column=0, sticky="w", pady=4)
            self.funcionario_bloqueio = ttk.Combobox(left, values=[], width=25)
            self.funcionario_bloqueio.grid(row=14, column=1, sticky="ew", pady=4)

            ttk.Label(left, text="Data").grid(row=15, column=0, sticky="w", pady=4)
            self.data_bloqueio = ttk.Entry(left, width=28)
            self.data_bloqueio.grid(row=15, column=1, sticky="ew", pady=4)
            self.data_bloqueio.insert(0, "2026-10-15")

            ttk.Button(left, text="Bloquear dia", command=self.bloquear_dia_ui).grid(
                row=16, column=0, columnspan=2, sticky="ew", pady=(8, 4)
            )

            ttk.Label(left, text="Data importante").grid(row=17, column=0, sticky="w", pady=4)
            self.data_importante = ttk.Entry(left, width=28)
            self.data_importante.grid(row=17, column=1, sticky="ew", pady=4)
            self.data_importante.insert(0, "2026-10-20")

            ttk.Button(left, text="Marcar dia importante", command=self.marcar_dia_importante_ui).grid(
                row=18, column=0, columnspan=2, sticky="ew", pady=(8, 4)
            )

            ttk.Label(left, text="Grupo para funcionário").grid(row=19, column=0, sticky="w", pady=4)
            self.nome_grupo = ttk.Entry(left, width=28)
            self.nome_grupo.grid(row=19, column=1, sticky="ew", pady=4)

            ttk.Label(left, text="Nome do funcionário").grid(row=20, column=0, sticky="w", pady=4)
            self.nome_func_grupo = ttk.Entry(left, width=28)
            self.nome_func_grupo.grid(row=20, column=1, sticky="ew", pady=4)

            ttk.Button(left, text="Definir grupo", command=self.definir_grupo_ui).grid(
                row=21, column=0, columnspan=2, sticky="ew", pady=(8, 4)
            )

            ttk.Label(right, text="Funcionários cadastrados", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 6))
            self.lista_funcionarios = tk.Listbox(right, width=60, height=18, font=("Consolas", 10))
            self.lista_funcionarios.pack(fill="both", expand=True)

            ttk.Label(right, text="Período da escala", font=("Arial", 12, "bold")).pack(anchor="w", pady=(12, 6))
            period_frame = ttk.Frame(right)
            period_frame.pack(fill="x", pady=4)

            ttk.Label(period_frame, text="Início").grid(row=0, column=0, sticky="w", padx=(0, 8))
            self.data_inicio = ttk.Entry(period_frame, width=18)
            self.data_inicio.grid(row=0, column=1, sticky="w")
            self.data_inicio.insert(0, "2026-10-06")

            ttk.Label(period_frame, text="Fim").grid(row=0, column=2, sticky="w", padx=(8, 8))
            self.data_fim = ttk.Entry(period_frame, width=18)
            self.data_fim.grid(row=0, column=3, sticky="w")
            self.data_fim.insert(0, "2026-10-12")

            ttk.Button(right, text="Gerar escala", command=self.gerar_escala_ui).pack(fill="x", pady=(8, 8))

            ttk.Label(right, text="Resultado", font=("Arial", 12, "bold")).pack(anchor="w", pady=(8, 6))
            self.resultado = scrolledtext.ScrolledText(right, width=80, height=18, wrap=tk.WORD)
            self.resultado.pack(fill="both", expand=True)

            self.atualizar_combo_funcionarios()

        def atualizar_lista_funcionarios(self) -> None:
            self.lista_funcionarios.delete(0, tk.END)
            for func in self.gerenciador.funcionarios:
                self.lista_funcionarios.insert(tk.END, f"{func.nome} | {func.cargo} | Grupo: {func.grupo or 'sem grupo'}")
            self.atualizar_combo_funcionarios()

        def atualizar_combo_funcionarios(self) -> None:
            nomes = [func.nome for func in self.gerenciador.funcionarios]
            self.funcionario_bloqueio['values'] = nomes
            if nomes:
                self.funcionario_bloqueio.set(nomes[0])

        def adicionar_funcionario_ui(self) -> None:
            try:
                nome = self.entradas["Nome"].get().strip()
                cargo = self.entradas["Cargo"].get().strip()
                prioridade = int(self.entradas["Prioridade"].get() or "1")
                grupo = self.entradas["Grupo"].get().strip() or None
                tipo = self.entradas["Tipo da escala"].get().strip() or "dias_trabalho"
                dias_trabalho = int(self.entradas["Dias trabalho alvo"].get() or "5")
                dias_folga = int(self.entradas["Dias folga alvo"].get() or "2")

                self.gerenciador.adicionar_funcionario(
                    nome=nome,
                    cargo=cargo,
                    prioridade=prioridade,
                    grupo=grupo,
                    escala_tipo=tipo,
                    dias_trabalho_alvo=dias_trabalho,
                    dias_folga_alvo=dias_folga,
                )
                self.atualizar_lista_funcionarios()
                self.limpar_formulario()
                messagebox.showinfo("Sucesso", "Funcionário adicionado com sucesso.")
            except ValueError as exc:
                messagebox.showerror("Erro", str(exc))

        def limpar_formulario(self) -> None:
            for campo in ["Nome", "Cargo", "Prioridade", "Grupo", "Tipo da escala", "Dias trabalho alvo", "Dias folga alvo"]:
                self.entradas[campo].delete(0, tk.END)
            self.entradas["Prioridade"].insert(0, "1")
            self.entradas["Tipo da escala"].insert(0, "dias_trabalho")
            self.entradas["Dias trabalho alvo"].insert(0, "5")
            self.entradas["Dias folga alvo"].insert(0, "2")

        def aplicar_tipo_global(self) -> None:
            try:
                self.gerenciador.definir_tipo_escala_global(self.tipo_global.get())
                messagebox.showinfo("Sucesso", f"Tipo global definido: {self.tipo_global.get()}")
            except ValueError as exc:
                messagebox.showerror("Erro", str(exc))

        def bloquear_dia_ui(self) -> None:
            funcionario = self.funcionario_bloqueio.get().strip()
            data = self.data_bloqueio.get().strip()
            if not funcionario or not data:
                messagebox.showerror("Erro", "Escolha um funcionário e informe uma data.")
                return
            try:
                self.gerenciador.bloquear_dia(funcionario, data)
                messagebox.showinfo("Sucesso", f"Dia {data} bloqueado para {funcionario}.")
            except ValueError as exc:
                messagebox.showerror("Erro", str(exc))

        def marcar_dia_importante_ui(self) -> None:
            data = self.data_importante.get().strip()
            if not data:
                messagebox.showerror("Erro", "Informe uma data importante.")
                return
            self.gerenciador.marcar_dia_importante(data)
            messagebox.showinfo("Sucesso", f"Dia {data} marcado como importante.")

        def definir_grupo_ui(self) -> None:
            nome = self.nome_func_grupo.get().strip()
            grupo = self.nome_grupo.get().strip()
            if not nome or not grupo:
                messagebox.showerror("Erro", "Informe o nome do funcionário e o nome do grupo.")
                return
            try:
                self.gerenciador.definir_grupo(nome, grupo)
                self.atualizar_lista_funcionarios()
                messagebox.showinfo("Sucesso", f"Funcionário {nome} vinculado ao grupo {grupo}.")
            except ValueError as exc:
                messagebox.showerror("Erro", str(exc))

        def gerar_escala_ui(self) -> None:
            inicio = self.data_inicio.get().strip()
            fim = self.data_fim.get().strip()

            try:
                escala = self.gerenciador.gerar_escala(inicio, fim)
                linhas: List[str] = ["ESCALA GERADA\n"]
                for dia, dados in escala.items():
                    linhas.append(f"{dia}:")
                    linhas.append(f"  Trabalho: {', '.join(dados['trabalho']) if dados['trabalho'] else 'Nenhum'}")
                    linhas.append(f"  Folga: {', '.join(dados['folga']) if dados['folga'] else 'Nenhum'}")
                    linhas.append("")
                self.resultado.delete("1.0", tk.END)
                self.resultado.insert(tk.END, "\n".join(linhas).strip())
                messagebox.showinfo("Sucesso", "Escala gerada com sucesso.")
            except ValueError as exc:
                messagebox.showerror("Erro", str(exc))


if __name__ == "__main__":
    if tk is not None:
        app = EscalaApp()
        app.mainloop()
    else:
        menu()
