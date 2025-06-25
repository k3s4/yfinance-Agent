"""
サマリーレポート生成モジュール

このモジュールは、ワークフロー完了後に美しいサマリーレポートを生成します。
全エージェントの分析結果を統合し、視覚的に魅力的な形式で表示します。
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.utils.logging_config import setup_logger
from src.utils.agent_collector import extract_key_insights

# ロガーを設定
logger = setup_logger('summary_report')

# レポート用記号とスタイル
REPORT_SYMBOLS = {
    "header": "█",
    "subheader": "▓",
    "border": "═",
    "separator": "─",
    "bullet": "●",
    "arrow": "→",
    "check": "✓",
    "cross": "✗",
    "star": "★",
    "diamond": "◆"
}

# シグナル・アクション用のアイコン
SIGNAL_ICONS = {
    "bullish": "🔺",
    "bearish": "🔻", 
    "neutral": "⚪",
    "buy": "🟢",
    "sell": "🔴",
    "hold": "🟡",
    "high": "🔴",
    "medium": "🟡",
    "low": "🟢"
}

# エージェント情報
AGENT_INFO = {
    "technical_analysis": {"name": "テクニカル分析", "icon": "📈"},
    "fundamental_analysis": {"name": "ファンダメンタル分析", "icon": "📊"},  
    "sentiment_analysis": {"name": "センチメント分析", "icon": "💭"},
    "valuation_analysis": {"name": "バリュエーション分析", "icon": "💰"},
    "risk_analysis": {"name": "リスク分析", "icon": "⚠️"},
    "debate_analysis": {"name": "議論・合意形成", "icon": "🗣️"},
    "final_recommendation": {"name": "最終投資判断", "icon": "🎯"}
}


class SummaryReportGenerator:
    """サマリーレポート生成クラス"""
    
    def __init__(self):
        """初期化"""
        self.width = 100
        self.half_width = self.width // 2
        
    def _create_header(self, title: str, level: int = 1) -> str:
        """ヘッダーを作成する"""
        if level == 1:
            symbol = REPORT_SYMBOLS["header"]
            border = symbol * self.width
            title_line = f"{symbol * 3} {title} {symbol * (self.width - len(title) - 6)}"
            return f"{border}\n{title_line}\n{border}"
        else:
            symbol = REPORT_SYMBOLS["subheader"]
            title_line = f"{symbol * 2} {title}"
            separator = REPORT_SYMBOLS["separator"] * (self.width - 2)
            return f"{title_line}\n{separator}"
    
    def _format_percentage(self, value: float) -> str:
        """パーセンテージをフォーマットする"""
        if isinstance(value, (int, float)):
            if -1 <= value <= 1:
                return f"{value:.1%}"
            else:
                return f"{value:.2f}"
        return str(value)
    
    def _get_signal_display(self, signal: str) -> str:
        """シグナルの表示形式を取得する"""
        if not signal:
            return "⚪ 不明"
        
        icon = SIGNAL_ICONS.get(signal.lower(), "⚪")
        return f"{icon} {signal.upper()}"
    
    def _format_key_metrics(self, data: Dict[str, Any]) -> List[str]:
        """主要指標をフォーマットする"""
        lines = []
        
        # 最終判断
        final_rec = data.get('final_recommendation', {})
        if final_rec:
            action = final_rec.get('action', 'HOLD')
            confidence = final_rec.get('confidence', 0.0)
            lines.append(f"最終判断: {self._get_signal_display(action)} (信頼度: {self._format_percentage(confidence)})")
        
        # 主要指標
        insights = extract_key_insights({'data': data})
        if insights:
            lines.append(f"技術的シグナル: {self._get_signal_display(insights.get('technical_signal', 'neutral'))}")
            lines.append(f"市場感情: {self._get_signal_display(insights.get('market_sentiment', 'neutral'))}")
            lines.append(f"リスクレベル: {SIGNAL_ICONS.get(insights.get('risk_level', 'medium'), '🟡')} {insights.get('risk_level', 'MEDIUM').upper()}")
        
        return lines
    
    def _format_agent_summary(self, agent_key: str, agent_data: Any) -> List[str]:
        """エージェントサマリーをフォーマットする"""
        lines = []
        
        agent_info = AGENT_INFO.get(agent_key, {"name": agent_key, "icon": "📋"})
        header = f"{agent_info['icon']} {agent_info['name']}"
        lines.append(header)
        lines.append("─" * len(header))
        
        if isinstance(agent_data, dict):
            # シグナルと信頼度を表示
            if 'signal' in agent_data:
                signal = agent_data['signal']
                lines.append(f"  シグナル: {self._get_signal_display(signal)}")
            
            if 'confidence' in agent_data:
                confidence = agent_data['confidence'] 
                lines.append(f"  信頼度: {self._format_percentage(confidence)}")
            
            # その他の重要な指標
            important_keys = ['action', 'risk_level', 'score', 'sentiment', 'recommendation']
            for key in important_keys:
                if key in agent_data and key not in ['signal', 'confidence']:
                    value = agent_data[key]
                    if key == 'action':
                        lines.append(f"  アクション: {self._get_signal_display(value)}")
                    elif key == 'risk_level':
                        lines.append(f"  リスク: {SIGNAL_ICONS.get(str(value).lower(), '🟡')} {str(value).upper()}")
                    else:
                        if isinstance(value, (int, float)):
                            lines.append(f"  {key}: {self._format_percentage(value)}")
                        else:
                            lines.append(f"  {key}: {value}")
            
            # 理由や分析内容
            if 'reasoning' in agent_data:
                reasoning = agent_data['reasoning']
                if isinstance(reasoning, str) and len(reasoning) > 0:
                    lines.append("  理由:")
                    # 長い文章を適切に改行
                    words = reasoning.split()
                    current_line = "    "
                    for word in words:
                        if len(current_line + word) > self.width - 4:
                            lines.append(current_line.rstrip())
                            current_line = f"    {word} "
                        else:
                            current_line += f"{word} "
                    if current_line.strip():
                        lines.append(current_line.rstrip())
        
        elif isinstance(agent_data, str):
            # 文字列の場合は適切に改行
            words = agent_data.split()
            current_line = "  "
            for word in words:
                if len(current_line + word) > self.width - 2:
                    lines.append(current_line.rstrip())
                    current_line = f"  {word} "
                else:
                    current_line += f"{word} "
            if current_line.strip():
                lines.append(current_line.rstrip())
        
        return lines
    
    def _generate_executive_summary(self, enhanced_state: Dict[str, Any]) -> str:
        """エグゼクティブサマリーを生成する"""
        lines = []
        lines.append(self._create_header("📋 エグゼクティブサマリー", 2))
        
        data = enhanced_state.get('data', {})
        metadata = enhanced_state.get('report_metadata', {})
        
        # 基本情報
        ticker = metadata.get('ticker', '不明')
        analysis_period = metadata.get('analysis_period', {})
        lines.append(f"銘柄コード: {ticker}")
        
        if analysis_period.get('start_date') and analysis_period.get('end_date'):
            lines.append(f"分析期間: {analysis_period['start_date']} ～ {analysis_period['end_date']}")
        
        lines.append("")
        
        # 主要指標
        key_metrics = self._format_key_metrics(data)
        for metric in key_metrics:
            lines.append(f"{REPORT_SYMBOLS['bullet']} {metric}")
        
        return "\n".join(lines)
    
    def _generate_detailed_analysis(self, enhanced_state: Dict[str, Any]) -> str:
        """詳細分析を生成する"""
        lines = []
        lines.append(self._create_header("🔍 詳細分析", 2))
        
        data = enhanced_state.get('data', {})
        processed_agents = enhanced_state.get('processed_agents', {})
        
        # 分析順序
        analysis_order = [
            'technical_analysis',
            'fundamental_analysis', 
            'sentiment_analysis',
            'valuation_analysis',
            'risk_analysis',
            'debate_analysis'
        ]
        
        for i, analysis_key in enumerate(analysis_order):
            if analysis_key in data:
                if i > 0:
                    lines.append("")  # セクション間の空行
                
                agent_lines = self._format_agent_summary(analysis_key, data[analysis_key])
                lines.extend(agent_lines)
        
        return "\n".join(lines)
    
    def _generate_final_recommendation(self, enhanced_state: Dict[str, Any]) -> str:
        """最終推奨を生成する"""
        lines = []
        lines.append(self._create_header("🎯 最終投資推奨", 2))
        
        data = enhanced_state.get('data', {})
        final_rec = data.get('final_recommendation', {})
        
        if final_rec:
            action = final_rec.get('action', 'HOLD')
            confidence = final_rec.get('confidence', 0.0)
            position_size = final_rec.get('position_size', 0.0)
            
            lines.append(f"推奨アクション: {self._get_signal_display(action)}")
            lines.append(f"信頼度: {self._format_percentage(confidence)}")
            lines.append(f"推奨ポジションサイズ: {self._format_percentage(position_size)}")
            
            # その他の推奨事項
            other_recommendations = [
                ('target_price', '目標価格'),
                ('stop_loss', 'ストップロス'),
                ('time_horizon', '投資期間'),
                ('risk_level', 'リスクレベル')
            ]
            
            for key, label in other_recommendations:
                if key in final_rec:
                    value = final_rec[key]
                    if key == 'risk_level':
                        lines.append(f"{label}: {SIGNAL_ICONS.get(str(value).lower(), '🟡')} {str(value).upper()}")
                    else:
                        lines.append(f"{label}: {value}")
        
        # 投資判断の詳細説明
        investment_decision = data.get('investment_decision')
        if investment_decision and isinstance(investment_decision, str):
            lines.append("")
            lines.append("詳細説明:")
            # 適切に改行
            words = investment_decision.split()
            current_line = ""
            for word in words:
                if len(current_line + word) > self.width - 2:
                    lines.append(current_line.rstrip())
                    current_line = f"{word} "
                else:
                    current_line += f"{word} "
            if current_line.strip():
                lines.append(current_line.rstrip())
        
        return "\n".join(lines)
    
    def generate_report(self, enhanced_state: Dict[str, Any]) -> str:
        """完全なレポートを生成する"""
        sections = []
        
        # メインヘッダー
        metadata = enhanced_state.get('report_metadata', {})
        ticker = metadata.get('ticker', '不明')
        title = f"AI投資分析レポート - {ticker}"
        sections.append(self._create_header(title))
        sections.append("")
        
        # 生成日時
        generated_at = metadata.get('generated_at')
        if generated_at:
            try:
                dt = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%Y年%m月%d日 %H:%M:%S')
                sections.append(f"生成日時: {formatted_time}")
                sections.append("")
            except:
                pass
        
        # エグゼクティブサマリー
        sections.append(self._generate_executive_summary(enhanced_state))
        sections.append("")
        sections.append("")
        
        # 詳細分析
        sections.append(self._generate_detailed_analysis(enhanced_state))
        sections.append("")
        sections.append("")
        
        # 最終推奨
        sections.append(self._generate_final_recommendation(enhanced_state))
        sections.append("")
        
        # フッター
        sections.append(REPORT_SYMBOLS["border"] * self.width)
        sections.append("このレポートはAI金融分析システムによって自動生成されました")
        sections.append(REPORT_SYMBOLS["border"] * self.width)
        
        return "\n".join(sections)


# グローバルインスタンス
report_generator = SummaryReportGenerator()


def print_summary_report(enhanced_state: Dict[str, Any]) -> None:
    """
    サマリーレポートを生成して表示する
    
    Args:
        enhanced_state: 拡張された最終状態データ
    """
    try:
        report = report_generator.generate_report(enhanced_state)
        
        # ログとして記録（INFOレベルでコンソールに表示される）
        logger.info("\n" + report)
        
        # コンソールにも直接出力
        print("\n" + report)
        
    except Exception as e:
        logger.error(f"サマリーレポートの生成中にエラーが発生しました: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


def generate_summary_report(enhanced_state: Dict[str, Any]) -> str:
    """
    サマリーレポートを生成して文字列として返す
    
    Args:
        enhanced_state: 拡張された最終状態データ
        
    Returns:
        生成されたレポートの文字列
    """
    try:
        return report_generator.generate_report(enhanced_state)
    except Exception as e:
        logger.error(f"サマリーレポートの生成中にエラーが発生しました: {str(e)}")
        return f"レポート生成エラー: {str(e)}"