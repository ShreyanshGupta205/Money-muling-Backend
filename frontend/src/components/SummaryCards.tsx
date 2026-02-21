import React from "react";

interface Summary {
    total_accounts_analyzed: number;
    suspicious_accounts_flagged: number;
    fraud_rings_detected: number;
    processing_time_seconds: number;
}

interface Props {
    summary: Summary;
}

const cards = [
    {
        key: "total_accounts_analyzed" as const,
        label: "Accounts Analyzed",
        icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
        ),
        color: "text-accent-cyan",
        bg: "bg-accent-cyan/10",
        border: "border-accent-cyan/20",
    },
    {
        key: "suspicious_accounts_flagged" as const,
        label: "Suspicious Flagged",
        icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        ),
        color: "text-accent-rose",
        bg: "bg-accent-rose/10",
        border: "border-accent-rose/20",
    },
    {
        key: "fraud_rings_detected" as const,
        label: "Fraud Rings",
        icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101M10.172 13.828a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
        ),
        color: "text-accent-amber",
        bg: "bg-accent-amber/10",
        border: "border-accent-amber/20",
    },
    {
        key: "processing_time_seconds" as const,
        label: "Processing Time",
        icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        ),
        color: "text-accent-emerald",
        bg: "bg-accent-emerald/10",
        border: "border-accent-emerald/20",
        suffix: "s",
    },
];

export default function SummaryCards({ summary }: Props) {
    return (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 stagger">
            {cards.map((c) => (
                <div
                    key={c.key}
                    className={`relative overflow-hidden glass-card p-6 border ${c.border} hover:bg-white/[0.02] transition-colors animate-fade-in-up opacity-0 shadow-lg`}
                >
                    <div className={`absolute -top-12 -right-12 w-32 h-32 rounded-full blur-3xl ${c.bg} opacity-50 pointer-events-none`} />
                    <div className="relative z-10">
                        <div className="flex items-center gap-3 mb-3">
                            <div className={`w-10 h-10 rounded-xl ${c.bg} flex items-center justify-center ${c.color} shadow-inner`}>
                                {c.icon}
                            </div>
                        </div>
                        <p className="text-2xl font-bold text-text-primary">
                            {summary[c.key]}
                            {c.suffix && (
                                <span className="text-sm font-normal text-text-secondary ml-0.5">
                                    {c.suffix}
                                </span>
                            )}
                        </p>
                        <p className="text-xs text-text-secondary mt-1 font-medium tracking-wide uppercase">{c.label}</p>
                    </div>
                </div>
            ))}
        </div>
    );
}
