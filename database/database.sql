CREATE TABLE sample_entity_status(
    id		                        SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO sample_entity_status (enumerator) VALUES
	 ('created'),
     ('pending'),
	 ('success'),
     ('failed');

CREATE TABLE sample_entity(
    id                     SERIAL PRIMARY KEY,
    sample_entity_key      CHAR(36) NOT NULL,
    status_id              INTEGER NOT NULL REFERENCES sample_entity_status(id),
    sample_entity_data     JSONB NOT NULL,
    counter                INTEGER NOT NULL,
    created_at             TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(sample_entity_key)
);

CREATE TABLE sample_entity_status_event(
    id                              SERIAL PRIMARY KEY,
    sample_entity_id                INTEGER NOT NULL REFERENCES sample_entity(id),
    status_id                       INTEGER NOT NULL REFERENCES sample_entity_status(id),
    event_datetime                  TIMESTAMP NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW())
);