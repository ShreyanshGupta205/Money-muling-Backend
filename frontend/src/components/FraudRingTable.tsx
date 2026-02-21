import React from "react";

interface FraudRing {
    ring_id: string;
    member_accounts: string[];
    pattern_type: string;
    risk_score: number;
}

interface Props {
    rings: FraudRing[];
}

export default function FraudRingTable({ rings }: Props) {
    if (rings.length === 0) {
        return (
            <p className="text-text-secondary text-sm">
                No fraud rings detected.
            </p>
        );
    }

    return (
        <div className="overflow-x-auto">
            <table className="w-full forensic-table">
                <thead>
                    <tr>
                        <th>Ring ID</th>
                        <th>Pattern Type</th>
                        <th>Member Count</th>
                        <th>Risk Score</th>
                        <th>Member Accounts</th>
                    </tr>
                </thead>
                <tbody>
                    {rings.map((ring) => (
                        <tr key={ring.ring_id}>
                            <td className="font-mono text-accent-violet font-semibold">
                                {ring.ring_id}
                            </td>
                            <td>
                                <span className="inline-block px-3 py-1.5 rounded-md bg-accent-rose/10 border border-accent-rose/20 text-accent-rose text-xs font-bold uppercase tracking-wider shadow-inner">
                                    {ring.pattern_type}
                                </span>
                            </td>
                            <td className="text-text-primary font-medium">
                                {ring.member_accounts.length}
                            </td>
                            <td>
                                <div className="flex items-center gap-2">
                                    <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden max-w-[80px]">
                                        <div
                                            className="h-full rounded-full transition-all duration-1000 ease-out shadow-[0_0_8px_rgba(255,255,255,0.2)]"
                                            style={{
                                                width: `${ring.risk_score}%`,
                                                background:
                                                    ring.risk_score >= 70
                                                        ? "linear-gradient(90deg, #f43f5e, #be123c)"
                                                        : ring.risk_score >= 40
                                                            ? "linear-gradient(90deg, #f59e0b, #b45309)"
                                                            : "linear-gradient(90deg, #06b6d4, #0369a1)",
                                            }}
                                        />
                                    </div>
                                    <span
                                        className={`text-xs font-bold ${ring.risk_score >= 70
                                            ? "text-accent-rose"
                                            : ring.risk_score >= 40
                                                ? "text-accent-amber"
                                                : "text-accent-cyan"
                                            }`}
                                    >
                                        {ring.risk_score}
                                    </span>
                                </div>
                            </td>
                            <td className="font-mono text-xs text-text-secondary max-w-xs truncate">
                                {ring.member_accounts.join(", ")}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
