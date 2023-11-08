CREATE TABLE tasks (
  task_id SERIAL PRIMARY KEY,
  description TEXT NOT NULL,
  completed BOOLEAN NOT NULL DEFAULT false
);