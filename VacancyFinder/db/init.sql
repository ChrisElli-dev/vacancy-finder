CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    wage INTEGER,
    type_of_employment VARCHAR(50),
    expertise TEXT,
    updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS applicants (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255),
    desired_role VARCHAR(255),
    expertise TEXT,
    expected_wage INTEGER,
    type_of_employment VARCHAR(50),
    updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
