First of all, thank you for viewing this project.

This project is the result of my 8 hours marathon on showcasing my technical skills regarding REST APIs, Database and
coding. Thankfully with the help of powerful AI models I was able to focus on the business logic while letting them handle
trivial tasks which made the process much quicker.

Let's talk about the code stub first. This Flask code stub is the baseline of my many recent projects that I have built.
It has everything you need to start developing without having to attach this library, that library ... just to write a
Hello World API. Config is layered (`default.py` -> `testing.py` -> `environment.py`) so local secrets never reach git,
every API returns the same `{code, data, message}` envelope through `respond_with_code`, errors are classes with their own
response code instead of magic numbers scattered around, query/body validation comes from marshmallow through a small
`use_kwargs` wrapper that also feeds Swagger, and there are ready-made modules for MinIO/S3 uploads, caching and DB
querying. So you can certainly build any app from scratch, whether you are a senior or a junior.

Now let's jump into the project.

Upon reading the requirements I was heavily mistaken that for each of the Dog Breed here there should only be 1 image and
the users can replace them making 1 Breed = 1 Image only. For 3 hours straight setting this project up (MySQL, data models,
data init functions...) I've thought about it a lot and when I'm done i immediately looked back just to find out my instinct was correct: The requirements
refers to a social-app like for dog owners which supports uploading dog images and let the users attach their image to a breed which
I got from The Dog API upon firing up the server for the first time.

So I went back to update the data models and this took a lot of time as I had to also deal with file uploading (luckily
for this code stub I already wrote a module for uploading to MinIO which is also compatible with AWS S3 API calls). Dealing with
APIs, data models and helpers, module functions, methods ...etc for at the same time - with a deadline is very stressful
(but It really made coding fun again haha) so i described what are the intended outputs of my APIs to Claude and it did
all the test units for me, then I read them back and fixed the ones that tested the wrong thing.

## How it ended up

The import is one shot, like the requirement says: `python3 manage.py init-data` creates the tables, seeds 3 demo users and
pulls all 631 breeds from The Dog API. No cron, no sync, nothing clever.

For the images I ended up with two separate ideas, because after the misunderstanding above I think both are needed:

- `BreedImage` is the breed's own picture (the one that comes from The Dog API, or one you replace it with). A breed has
  exactly one, so `Breed.image_id` is just a column.
- `DogImage` is the user gallery - my dog, your dog, many dogs per breed, each one owned by the user who uploaded it. This
  is the part that makes it feel like a social app.

Uploading is server side in 2 steps: `POST /frontend/upload/image` sends the bytes to MinIO and gives you back a `file_id`,
then you attach that file to a breed (`/frontend/dog/breed/image`) or post it to the gallery (`/frontend/dog/image`). I kept
them separate because a file is a file - the same upload endpoint can later serve avatars or anything else without touching
the dog code.

Deleting is a soft delete (`status = Deleted`). I did not remove the object from MinIO, on purpose: in a real product you
want the file around for a while in case someone deletes by accident, and a cleanup job can sweep it later.

The bucket is public-read, so `image.url` opens directly in the browser, which is what the last user story asks for. I also
had to pass the real byte length and the image content type to MinIO - without them it happily stores a 0 byte object and
still answers 200, which cost me a good while to notice.

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

A few notes from me to you, mostly the things I wish somebody had told me while I was building this. Hopefully they save
you a bit of time.

- **MinIO.** If you have not run it before it is really painless: `brew install minio minio-mc && brew services start minio`,
  then log in with `minioadmin` / `minioadmin`, make the `assessment-files` bucket and set it to `download`. That last bit
  is what lets the images open straight in the browser, so please do not skip it.
- **Schema changes go through Alembic**, not `create_all()`. If you already have the tables from an earlier run, do not
  panic when `db upgrade` complains - just run `python3 manage.py db stamp head` once and you are back on track.
- **Every response is HTTP 200, even the errors**, so please look at `code` in the body instead of the status. 0 means it
  worked, and I grouped the rest so they are easy to recognise: 100-199 user, 200-299 dog, 300-399 file, 2 invalid argument.
- **Poking around is easiest through Swagger** at `/frontend/swagger/` and `/admin/swagger/`. If you prefer a file, the
  `openapi.yaml` in the repo is generated from the app itself (`python3 scripts/gen_openapi.py`), so it can never quietly
  drift away from the code.
- **The tests are just `python3 -m pytest`** - 161 of them, around 94% coverage, and the run fails on purpose if it drops
  below 90%. Feel free to break something and watch them shout at you, that is the fun part.

Thanks again for reading, and I hope the dogs made it worth it :D.
