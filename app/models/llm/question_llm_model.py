from pydantic import BaseModel, Field
from typing import Annotated, Any, Optional
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
import operator
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from app.models.llm.base_llm_model import BaseLLMModel
from langgraph.graph.state import CompiledStateGraph
from app.core.logging import NaviApiLog


class State(BaseModel):
    query: str
    messages: Annotated[list[BaseMessage], operator.add] = Field(default=[])


class QuestionLLMModel(BaseLLMModel):
    def __init__(self, file_paths: list[str], collection_name: str = "manuals") -> None:
        """
        質問応答用のLLMモデルを初期化する
        
        Args:
            file_paths: フィルタリングするファイルパスのリスト
            collection_name: 使用するコレクション名
            
        Raises:
            ValueError: question_llm_settingの設定値が不正な場合
            Exception: 初期化に失敗した場合
        """
        super().__init__(file_paths=file_paths, collection_name=collection_name)
        
        try:
            self.question_llm_setting = self.params.get_parameter("question_llm_setting")
            if not self.question_llm_setting:
                raise KeyError("question_llm_settingがSSMに設定されていません")
            
            # 必須設定値の検証
            required_keys = ["system_context", "prompt_context"]
            missing_keys = [key for key in required_keys if not self.question_llm_setting.get(key)]
            if missing_keys:
                raise KeyError(f"question_llm_settingに必須キーが不足しています: {', '.join(missing_keys)}")
                
            NaviApiLog.info("QuestionLLMModelを正常に初期化しました")
        except Exception as e:
            NaviApiLog.error(f"QuestionLLMModelの初期化に失敗しました: {e}")
            raise RuntimeError("質問応答モデルの初期化に失敗しました")

    def add_message(self, state: State) -> dict[str, Any]:
        """
        状態にメッセージを追加する
        
        Args:
            state: 現在の状態
            
        Returns:
            dict[str, Any]: 追加するメッセージを含む辞書
            
        Raises:
            Exception: メッセージの追加に失敗した場合
        """
        try:
            additional_messages = []
            if not state.messages:
                system_context = self.question_llm_setting.get("system_context")
                if not system_context:
                    NaviApiLog.warning("system_contextが空です。デフォルト値を使用します")
                    system_context = "あなたは親切なアシスタントです。"
                additional_messages.append(SystemMessage(content=system_context))
            
            if not state.query:
                NaviApiLog.warning("add_messageに空のクエリが提供されました")
                additional_messages.append(HumanMessage(content=""))
            else:
                additional_messages.append(HumanMessage(content=state.query))
            
            return {"messages": additional_messages}
        except Exception as e:
            NaviApiLog.error(f"メッセージの追加に失敗しました: {e}")
            raise RuntimeError("メッセージの処理に失敗しました")

    def llm_response(self, state: State) -> dict[str, Any]:
        """
        LLMを使用して応答を生成する
        
        Args:
            state: 現在の状態
            
        Returns:
            dict[str, Any]: 生成された応答を含む辞書
            
        Raises:
            Exception: 応答の生成に失敗した場合
        """
        try:
            if not state.query:
                NaviApiLog.warning("llm_responseに空のクエリが提供されました")
                return {"messages": [AIMessage(content="質問が空です。質問を入力してください。")]}
            
            prompt_context = self.question_llm_setting.get("prompt_context")
            if not prompt_context:
                raise KeyError("prompt_contextが設定されていません")
            
            prompt = ChatPromptTemplate.from_template(prompt_context)
            chain = RunnableParallel(
                {
                    "question": RunnablePassthrough(),
                    "context": self.retriever,
                }
            ).assign(answer=prompt | self.llm | StrOutputParser())
            
            output = chain.invoke(state.query)
            
            if not isinstance(output, dict):
                NaviApiLog.error(f"チェーンから予期しない出力タイプを受け取りました: {type(output)}")
                return {"messages": [AIMessage(content="回答の生成に失敗しました。")]}
            
            answer = output.get("answer")
            if not answer:
                NaviApiLog.warning("LLMから空の回答を受け取りました")
                answer = "回答を生成できませんでした。別の質問をお試しください。"
            
            NaviApiLog.info("LLM応答を正常に生成しました")
            return {"messages": [AIMessage(content=answer)]}
            
        except KeyError as e:
            NaviApiLog.error(f"LLM応答の設定エラー: {e}")
            raise KeyError("設定に不備があります")
        except Exception as e:
            NaviApiLog.error(f"LLM応答の予期しないエラー: {e}")
            raise RuntimeError("回答の生成中にエラーが発生しました")

    def get_graph(self) -> CompiledStateGraph:
        """
        LangGraphの実行グラフを構築して返す
        
        Returns:
            CompiledStateGraph: コンパイル済みの状態グラフ
            
        Raises:
            Exception: グラフの構築に失敗した場合
        """
        try:
            graph = StateGraph(State)
            graph.add_node("add_message", self.add_message)
            graph.add_node("llm_response", self.llm_response)

            graph.set_entry_point("add_message")
            graph.add_edge("add_message", "llm_response")
            graph.add_edge("llm_response", END)
            
            compiled_graph = graph.compile()
            NaviApiLog.info("LangGraphを正常にコンパイルしました")
            return compiled_graph
        except Exception as e:
            NaviApiLog.error(f"グラフのコンパイルに失敗しました: {e}")
            raise RuntimeError("グラフの構築に失敗しました")
