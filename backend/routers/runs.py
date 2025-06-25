from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Dict, Optional
from datetime import datetime

from backend.schemas import RunSummary, AgentSummary, AgentDetail, WorkflowFlow
from backend.storage.base import BaseLogStorage
from backend.dependencies import get_log_storage

"""
AIエージェントたちの実行ログを集約・可視化するAPI群を作成
BaseLogStorageを抽象的に扱っているので、インメモリからDBへの差し替えが容易
"""
router = APIRouter(
    prefix="/runs",
    tags=["Workflow Runs"]
)

@router.get("/", response_model=List[RunSummary])
async def list_runs(
    limit: int = Query(10, ge=1, le=100, description="取得する最大件数（1〜100）"),
    storage: BaseLogStorage = Depends(get_log_storage)
):
    """最近の実行履歴一覧を取得（ログストレージベース）

    BaseLogStorage（現在は InMemoryLogStorage）から AgentExecutionLog を取得し、
    最近完了したワークフロー実行の要約情報を返します。
    """
    try:
        # 全てのRun IDを取得
        run_ids = storage.get_unique_run_ids()

        # 各Run IDごとに要約データを構築
        results = []
        for run_id in run_ids[:limit]:
            agent_logs = storage.get_agent_logs(run_id=run_id)
            if not agent_logs:
                continue

            start_time = min(log.timestamp_start for log in agent_logs)
            end_time = max(log.timestamp_end for log in agent_logs)
            agents = sorted(set(log.agent_name for log in agent_logs))

            summary = RunSummary(
                run_id=run_id,
                start_time=start_time,
                end_time=end_time,
                agents_executed=agents,
                status="completed"
            )
            results.append(summary)

        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"実行履歴の取得に失敗しました: {str(e)}"
        )

@router.get("/{run_id}", response_model=RunSummary)
async def get_run(
    run_id: str = Path(..., description="取得対象のRun ID"),
    storage: BaseLogStorage = Depends(get_log_storage)
):
    """特定のRunの概要情報を取得（ログストレージベース）

    BaseLogStorage（現在は InMemoryLogStorage）から
    指定された run_id の AgentExecutionLog を取得し、
    実行概要を返します。
    """
    try:
        agent_logs = storage.get_agent_logs(run_id=run_id)
        if not agent_logs:
            raise HTTPException(
                status_code=404,
                detail=f"Run ID '{run_id}' のデータが見つかりません"
            )

        start_time = min(log.timestamp_start for log in agent_logs)
        end_time = max(log.timestamp_end for log in agent_logs)
        agents = sorted(set(log.agent_name for log in agent_logs))

        return RunSummary(
            run_id=run_id,
            start_time=start_time,
            end_time=end_time,
            agents_executed=agents,
            status="completed"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Run概要の取得に失敗しました: {str(e)}"
        )


@router.get("/{run_id}/agents", response_model=List[AgentSummary])
async def get_run_agents(
    run_id: str = Path(..., description="対象の実行ID"),
    storage: BaseLogStorage = Depends(get_log_storage)
):
    """指定された実行IDに紐づくすべてのAgentの実行状況を取得します（ログストレージベース）

    現在はInMemoryLogStorage（メモリ上のログ保存）を使用しています。
    """
    try:
        # 指定された実行IDのすべてのAgentログを取得
        agent_logs = storage.get_agent_logs(run_id=run_id)
        if not agent_logs:
            raise HTTPException(
                status_code=404,
                detail=f"実行ID「{run_id}」の情報が見つかりませんでした。"
            )

        # AgentSummary形式に変換
        results = []
        for log in agent_logs:
            summary = AgentSummary(
                agent_name=log.agent_name,
                start_time=log.timestamp_start,
                end_time=log.timestamp_end,
                execution_time_seconds=(log.timestamp_end - log.timestamp_start).total_seconds(),
                status="completed"  # 状態は必要に応じて変更してください
            )
            results.append(summary)

        # 開始時間順に並び替え
        results.sort(key=lambda x: x.start_time)
        return results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent実行情報の取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/{run_id}/agents/{agent_name}", response_model=AgentDetail)
async def get_agent_detail(
    run_id: str = Path(..., description="実行ID"),
    agent_name: str = Path(..., description="Agent名"),
    include_states: bool = Query(True, description="入出力状態を含めるか"),
    storage: BaseLogStorage = Depends(get_log_storage)
):
    """指定された実行IDとAgent名に対応する詳細な実行情報を取得します（ログストレージベース）

    現在はInMemoryLogStorage（メモリ上のログ保存）を使用しています。
    """
    try:
        # 該当するAgentのログを取得
        agent_logs = storage.get_agent_logs(run_id=run_id, agent_name=agent_name)
        if not agent_logs:
            raise HTTPException(
                status_code=404,
                detail=f"実行ID「{run_id}」内にAgent「{agent_name}」の記録が見つかりませんでした。"
            )

        # 関連するLLMの対話ログを取得
        llm_logs = storage.get_logs(run_id=run_id, agent_name=agent_name)
        llm_interaction_ids = [str(i) for i in range(len(llm_logs))] if llm_logs else []

        # 詳細情報を構築（基本的に1件のみ取得されるはず）
        log = agent_logs[0]
        result = AgentDetail(
            agent_name=log.agent_name,
            start_time=log.timestamp_start,
            end_time=log.timestamp_end,
            execution_time_seconds=(log.timestamp_end - log.timestamp_start).total_seconds(),
            status="completed",
            llm_interactions=llm_interaction_ids
        )

        # 状態や推論情報を含める場合
        if include_states:
            result.input_state = log.input_state
            result.output_state = log.output_state
            result.reasoning = log.reasoning_details

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agentの詳細情報取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/{run_id}/flow", response_model=WorkflowFlow)
async def get_workflow_flow(
    run_id: str = Path(..., description="実行ID"),
    storage: BaseLogStorage = Depends(get_log_storage)
):
    """指定された実行IDに対応する、全Agentの処理フローとデータの流れを取得します（ログベース）

    現在はInMemoryLogStorage（メモリ上での一時ログ保存）を使用しています。
    """
    try:
        # 実行IDに対応するすべてのAgentログを取得
        agent_logs = storage.get_agent_logs(run_id=run_id)
        if not agent_logs:
            raise HTTPException(
                status_code=404,
                detail=f"実行ID「{run_id}」に対応する情報が見つかりませんでした。"
            )

        # 実行全体の開始・終了時刻を取得
        start_time = min(log.timestamp_start for log in agent_logs)
        end_time = max(log.timestamp_end for log in agent_logs)

        # Agentごとの概要を構築
        agents = {}
        for log in agent_logs:
            agents[log.agent_name] = AgentSummary(
                agent_name=log.agent_name,
                start_time=log.timestamp_start,
                end_time=log.timestamp_end,
                execution_time_seconds=(log.timestamp_end - log.timestamp_start).total_seconds(),
                status="completed"  # 実際の状態に応じて変更可能
            )

        # 状態遷移（フロー）のリストを構築
        agent_logs_sorted = sorted(agent_logs, key=lambda x: x.timestamp_start)
        state_transitions = []

        for i, log in enumerate(agent_logs_sorted):
            transition = {
                "from_agent": "start" if i == 0 else agent_logs_sorted[i - 1].agent_name,
                "to_agent": log.agent_name,
                "state_size": len(str(log.input_state)) if log.input_state else 0,
                "timestamp": log.timestamp_start.isoformat()
            }
            state_transitions.append(transition)

        # 最後のAgentから「end」への遷移を追加
        if agent_logs_sorted:
            state_transitions.append({
                "from_agent": agent_logs_sorted[-1].agent_name,
                "to_agent": "end",
                "state_size": len(str(agent_logs_sorted[-1].output_state)) if agent_logs_sorted[-1].output_state else 0,
                "timestamp": agent_logs_sorted[-1].timestamp_end.isoformat()
            })

        # 最後のAgentの出力から「最終的な判断・アウトプット」を抽出（可能であれば）
        final_decision = None
        if agent_logs_sorted:
            last_log = agent_logs_sorted[-1]
            if last_log.output_state and isinstance(last_log.output_state, dict):
                messages = last_log.output_state.get("messages", [])
                if messages and len(messages) > 0:
                    last_message = messages[-1]
                    if isinstance(last_message, dict) and "content" in last_message:
                        final_decision = last_message["content"]

        return WorkflowFlow(
            run_id=run_id,
            start_time=start_time,
            end_time=end_time,
            agents=agents,
            state_transitions=state_transitions,
            final_decision=final_decision
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ワークフロー情報の取得中にエラーが発生しました: {str(e)}"
        )
