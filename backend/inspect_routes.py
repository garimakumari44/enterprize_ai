from app.api.v1.router import router


print("\n=== API V1 ROUTER ===")
print("Type:", type(router))
print("Prefix:", router.prefix)
print("Routes:", len(router.routes))


for i, included in enumerate(router.routes):
    print(f"\n{'=' * 80}")
    print(f"CHILD ROUTER {i}")
    print(f"{'=' * 80}")

    print("Type:", type(included))
    print("Dict keys:", list(included.__dict__.keys()))

    for key, value in included.__dict__.items():
        if key == "router":
            print("INNER ROUTER:", value)
            print(
                "INNER ROUTER TYPE:",
                type(value),
            )

            print(
                "INNER PREFIX:",
                getattr(value, "prefix", None),
            )

            print(
                "INNER ROUTE COUNT:",
                len(getattr(value, "routes", [])),
            )

            for route in getattr(value, "routes", []):
                print(
                    "   ROUTE:",
                    getattr(route, "path", None),
                    "| METHODS:",
                    getattr(route, "methods", None),
                    "| NAME:",
                    getattr(route, "name", None),
                )
        else:
            print(f"{key}: {value}")