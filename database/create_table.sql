CREATE TABLE colleges (
    college_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    college_tier VARCHAR(50),
    type VARCHAR(100),
    location VARCHAR(255),
    state VARCHAR(100),
    description TEXT,
    nirf_ranking INT,
    website_url VARCHAR(500)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    college_id INT NOT NULL,
    course_name VARCHAR(255) NOT NULL,
    duration_years DECIMAL(4,1),
    total_fee DECIMAL(12,2),
    annual_fee DECIMAL(12,2),
    intake_capacity INT,
    CONSTRAINT fk_courses_college
        FOREIGN KEY (college_id) REFERENCES colleges(college_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE eligibility_criteria (
    criteria_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    min_10th_pct DECIMAL(5,2),
    min_12th_pct DECIMAL(5,2),
    required_stream VARCHAR(100),
    accepted_exams VARCHAR(255),
    cutoff_rank_gen INT,
    cutoff_rank_reserved INT,
    CONSTRAINT fk_eligibility_course
        FOREIGN KEY (course_id) REFERENCES courses(course_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE admissions_logistics (
    logistics_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    application_start DATE,
    application_end DATE,
    required_docs TEXT,
    apply_link VARCHAR(500),
    admission_steps TEXT,
    CONSTRAINT fk_admissions_course
        FOREIGN KEY (course_id) REFERENCES courses(course_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
