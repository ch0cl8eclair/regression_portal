BEGIN;
CREATE TABLE "regr_developer" (
    "username" varchar(15) NOT NULL PRIMARY KEY,
    "username2" varchar(15),
    "firstname" varchar(15) NOT NULL,
    "surname" varchar(15) NOT NULL,
    "team" varchar(4) NOT NULL,
    "email" varchar(30) NOT NULL
)
;
CREATE TABLE "regr_responsibility" (
    "id" integer NOT NULL PRIMARY KEY,
    "package" varchar(20) NOT NULL,
    "function" varchar(30) NOT NULL,
    "team" varchar(4) NOT NULL,
    "primary_id" varchar(15) NOT NULL REFERENCES "regr_developer" ("username"),
    "secondary_id" varchar(15) NOT NULL REFERENCES "regr_developer" ("username"),
    "area" varchar(30)
)
;
ALTER TABLE "regr_release" ADD COLUMN
    "promoted" bool NOT NULL DEFAULT 0
;
ALTER TABLE "regr_release" ADD COLUMN
    "comment" varchar(100)
;
ALTER TABLE "regr_regressionresult" ADD COLUMN
    "date" datetime
;
ALTER TABLE "regr_regressionresult" ADD COLUMN
    "duration" varchar(3)
;
ALTER TABLE "regr_regressionresult" ADD COLUMN
    "start_time" varchar(8)
;

CREATE INDEX "regr_responsibility_72a128d" ON "regr_responsibility" ("primary_id");
CREATE INDEX "regr_responsibility_772a9b79" ON "regr_responsibility" ("secondary_id");
COMMIT;