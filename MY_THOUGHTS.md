First of all, thank you for viewing this project.

This project is the result of my 8 hours marathon on showcasing my technical skills regarding REST APIs, Database and
coding. Thankfully with the help of powerful AI models I was able to focus on the business logic while letting them handle
trivial tasks which made the process much quicker.

Let's talk about the code stub first. This Flask code stub is the baseline of my many recent projects, so I did not have to
attach this library, that library ... just to write a Hello World API. What it already gives me:

- **Layered config** (`default.py` -> `testing.py` -> `environment.py`) - local secrets stay out of git, and switching
  between local, testing and prod is one file, not a pile of if-else.
- **One response shape** `{code, data, message}` from `respond_with_code` - the client parses the same thing every time
  and I never write a response dict by hand.
- **Errors are classes with their own code** instead of magic numbers - raise it anywhere and it comes out formatted,
  which is also why adding the dog/file errors here took two minutes.
- **Validation that documents itself** - one `use_kwargs` declaration validates the request through marshmallow and
  generates the Swagger params from the same place, so they never go out of sync.
- **Modules I always end up needing**: MinIO/S3 uploads (same code works on AWS), caching, a model base with `to_dict`
  hooks and timestamps, Alembic, Babel, CORS.
- **Drop-in routing** - put a module under `app/api/frontend`, give it a `ns`, and it is registered and in Swagger with
  no wiring.
- **Users and auth are already there** - register, login, me, logout on the frontend side, plus the admin endpoints for
  listing users and changing their status. `@require_login` resolves the token, loads the user and refuses frozen or
  deleted accounts, so a new endpoint only needs the decorator.
- **Seeding built in** - `python3 manage.py init-data` creates the tables and fills them, so a fresh clone is usable in
  one command. Here I just plugged the breed import into it and it gave me the 631 breeds from The Dog API.

So you can certainly build any app from scratch with it, whether you are a senior or a junior.

Now let's jump into the project.

The short version of my 8 hours:

- **I read the requirements wrong at first** - I assumed 1 Breed = 1 Image, where a user just replaces the breed's picture.
- **3 hours went into the setup** with that assumption (MySQL, data models, data init from The Dog API).
- **Then it clicked**: this is a social app for dog owners, many users uploading many dogs to the same breed. My instinct
  had been nagging at me the whole time and it turned out to be right.
- **So I reworked the models** and added file uploading on top (luckily the stub already had my MinIO module, which speaks
  the AWS S3 API too, so that part was free).
- **Tests came last** - I described the intended output of each API to Claude, it wrote the test cases, then I read them
  back and fixed the ones that tested the wrong thing.

Juggling APIs, models, helpers and module functions all at once with a deadline is very stressful (but It really made
coding fun again haha).

## How it ended up

- **Two kinds of image**, because after the misunderstanding I think both are needed: `BreedImage` is the breed's own
  picture (one per breed, so `Breed.image_id` is just a column), `DogImage` is the user gallery - many dogs per breed,
  each owned by whoever uploaded it.
- **Upload is server side in 2 steps**: `/frontend/upload/image` sends the bytes to MinIO and returns a `file_id`, then
  you attach it to a breed or post it to the gallery. Keeping the upload generic means I can reuse it for avatars or
  anything else later.
- **Delete is soft** (`status = Deleted`) and the object stays in MinIO on purpose - people delete things by accident,
  a cleanup job can sweep it later.
- **The bucket is public-read** so `image.url` opens straight in the browser. Watch out: MinIO needs the real byte length
  and content type, otherwise it stores a 0 byte object and still answers 200 (that one cost me a while).
- **A random token instead of a JWT**: JWT is great when several services need to verify a token on their own, but this
  is one Flask app that already looks the user up on every request, so signing and parsing would be overkill here. 32
  random bytes kept server side do the same job, and I get free logout out of it.

## What I would improve with more time

- **The admin APIs have no authentication yet.** `/admin/user/users` is still WIDE open. The frontend ones all go through
  `@require_login`, admin just never got its own decorator.
- **The auth token cache is an in-process dict** (`app/caches/base.py`). `redis` is already in requirements, so this should
  be a real Redis backend - right now tokens die on restart and would not be shared between workers.
- **No endpoint to detach a breed image.** You can replace it, you can delete a gallery image, but you cannot clear
  `Breed.image_id` back to nothing.
- **`limit` is not capped.** `WEB_MAX_LIMIT = 200` sits in the config unused, so `?limit=100000` returns all 631 rows.
- **`imghdr` is deprecated** and gone in Python 3.13. `filetype` is already a dependency and does the same sniffing.
- **`init_breeds` commits once per breed** (631 commits) and assumes one page. It is fine at this size but batching, and
  reading the `Pagination-Count` header, would be the correct version.
- **Image width/height are not filled on upload** - that needs Pillow, and I did not want another dependency for it today.
- **Direct-to-MinIO presigned upload** would be better for big files, the helper already has `put_private_url` for it.
- A CI pipeline (GitHub Actions running pre-commit + pytest) would be the natural next step. Locally the same two run on
  commit and on push.

## Useful things to know

A few things I wish somebody had told me while building this, hopefully they save you some time.

- **MinIO** is painless: `brew install minio minio-mc && brew services start minio`, log in with `minioadmin` /
  `minioadmin`, create a bucket and set it to `download` so the images open in the browser - please DO NOT SKIP that part.
- **Schema changes go through Alembic**, not `create_all()`. If you already have the tables, do not panic when
  `db upgrade` complains, just run `python3 manage.py db stamp head` once.
- **Every response is HTTP 200, even the errors**, so read `code` in the body. 0 is success, the rest are grouped:
  100-199 user, 200-299 dog, 300-399 file, 2 invalid argument.
- **Swagger** is at `/frontend/swagger/` and `/admin/swagger/`, or `openapi.yaml` if you prefer a file - it is generated
  from the app (`python3 scripts/gen_openapi.py`) so it cannot drift.
- **Tests are just `python3 -m pytest`** - 161 of them, ~94% coverage, failing under 90% on purpose. Break something and
  watch them shout at you, that is the fun part.

Thanks again for reading, and I hope the dogs made it worth it ^_^.
