-- PostgreSQL Database Schema for X12 Messages (Simplified)
-- This schema stores complete decoded X12 messages as single rows

-- Drop table if exists (for clean setup)
DROP TABLE IF EXISTS x12_messages CASCADE;

-- X12 Messages Table - Stores complete decoded messages
CREATE TABLE x12_messages (
    id SERIAL PRIMARY KEY,

    -- Message Identification
    purchase_order_number VARCHAR(50),
    transaction_set_control_number VARCHAR(20),
    interchange_control_number VARCHAR(20),
    sender_id VARCHAR(50),
    receiver_id VARCHAR(50),

    -- Complete Message Data
    raw_x12_message TEXT NOT NULL,
    decoded_json TEXT NOT NULL,

    -- Metadata
    message_type VARCHAR(20) DEFAULT 'X12_850',
    status VARCHAR(20) DEFAULT 'received',
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(interchange_control_number, transaction_set_control_number)
);

-- Create Indexes for Performance
CREATE INDEX idx_x12_po_number ON x12_messages(purchase_order_number);
CREATE INDEX idx_x12_control_numbers ON x12_messages(interchange_control_number, transaction_set_control_number);
CREATE INDEX idx_x12_sender_receiver ON x12_messages(sender_id, receiver_id);
CREATE INDEX idx_x12_received_at ON x12_messages(received_at DESC);
-- GIN index for JSONB queries (cast TEXT to JSONB in queries)
-- CREATE INDEX idx_x12_decoded_json ON x12_messages USING GIN ((decoded_json::JSONB));

COMMENT ON TABLE x12_messages IS 'Stores complete decoded X12 messages with full JSON structure';
COMMENT ON COLUMN x12_messages.raw_x12_message IS 'Original X12 EDI message as received';
COMMENT ON COLUMN x12_messages.decoded_json IS 'Complete decoded X12 structure in JSON format (stored as TEXT, cast to JSONB for queries)';

-- Example queries using the TEXT column as JSONB:
-- SELECT id, decoded_json::JSONB->'ISA'->>'ISA13' as interchange_control FROM x12_messages;
-- SELECT * FROM x12_messages WHERE decoded_json::JSONB @> '{"ISA": {"ISA06": "CONTOSORETAIL"}}';
