CREATE TABLE IF NOT EXISTS agent_runs (
    id uuid PRIMARY KEY,
    message text NOT NULL,
    model text NOT NULL,
    status text NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    output jsonb,
    error_code text,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    completed_at timestamptz,
    CONSTRAINT agent_runs_result_check CHECK (
        (status = 'running' AND output IS NULL AND error_code IS NULL AND completed_at IS NULL)
        OR (status = 'succeeded' AND output IS NOT NULL AND error_code IS NULL AND completed_at IS NOT NULL)
        OR (status = 'failed' AND output IS NULL AND error_code IS NOT NULL AND completed_at IS NOT NULL)
    )
);
