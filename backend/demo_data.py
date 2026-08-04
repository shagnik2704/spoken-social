# ============================================================
# Demo fixtures for the admin comparison view
# ============================================================
# Static stand-in data served by /api/admin/comparison-metrics when the
# `programmes` table is empty (a fresh or unseeded database), so the dashboard
# renders something coherent instead of empty charts. Moved out of routes/admin.py,
# where it accounted for a quarter of the file.
#
# Nothing here touches the database. If the programmes table is populated, none of
# it is reachable.
# ============================================================

from typing import Optional


def get_mock_comparison_data(state: Optional[str] = None):
    state_key = state if state else "all"
    
    # Define state metrics
    data = {
        "all": {
            "fdp": {
                "colleges": 12, "students": 850, "progress": 72, "avgXP": 2450,
                "courses": {
                    "linux": {
                        "name": "Linux Administration",
                        "batches": {
                            "linux-2026-jan": {"name": "Jan-Apr 2026", "colleges": 6, "students": 450, "progress": 75, "avgXP": 2550},
                            "linux-2026-jul": {"name": "Jul-Oct 2026", "colleges": 6, "students": 400, "progress": 68, "avgXP": 2350}
                        }
                    },
                    "python": {
                        "name": "Python Programming",
                        "batches": {
                            "python-2026-feb": {"name": "Feb-May 2026", "colleges": 6, "students": 400, "progress": 68, "avgXP": 2350}
                        }
                    }
                }
            },
            "swayam_plus": {
                "colleges": 24, "students": 1850, "progress": 61, "avgXP": 1950,
                "courses": {
                    "webdev": {
                        "name": "Web Development",
                        "batches": {
                            "webdev-2026-jan": {"name": "Jan-Apr 2026", "colleges": 10, "students": 800, "progress": 64, "avgXP": 2100}
                        }
                    },
                    "ml": {
                        "name": "Machine Learning",
                        "batches": {
                            "ml-2026-feb": {"name": "Feb-May 2026", "colleges": 8, "students": 600, "progress": 55, "avgXP": 1800}
                        }
                    },
                    "cloud": {
                        "name": "Cloud Computing",
                        "batches": {
                            "cloud-2026-mar": {"name": "Mar-Jun 2026", "colleges": 6, "students": 450, "progress": 65, "avgXP": 1900}
                        }
                    }
                }
            },
            "ilw": {
                "colleges": 8, "students": 520, "progress": 85, "avgXP": 3200,
                "courses": {
                    "linux_adv": {
                        "name": "Linux Administration",
                        "batches": {
                            "linux-2026-jul": {"name": "Jul-Oct 2026", "colleges": 4, "students": 270, "progress": 88, "avgXP": 3350}
                        }
                    },
                    "cloud_adv": {
                        "name": "Cloud Computing",
                        "batches": {
                            "cloud-2026-mar": {"name": "Mar-Jun 2026", "colleges": 4, "students": 250, "progress": 82, "avgXP": 3050}
                        }
                    }
                }
            }
        },
        "Maharashtra": {
            "fdp": {
                "colleges": 4, "students": 280, "progress": 75, "avgXP": 2600,
                "courses": {
                    "linux": {
                        "name": "Linux Administration",
                        "batches": {
                            "linux-2026-jan": {"name": "Jan-Apr 2026", "colleges": 2, "students": 150, "progress": 78, "avgXP": 2700},
                            "linux-2026-jul": {"name": "Jul-Oct 2026", "colleges": 2, "students": 130, "progress": 72, "avgXP": 2500}
                        }
                    },
                    "python": {
                        "name": "Python Programming",
                        "batches": {
                            "python-2026-feb": {"name": "Feb-May 2026", "colleges": 2, "students": 130, "progress": 72, "avgXP": 2500}
                        }
                    }
                }
            },
            "swayam_plus": {
                "colleges": 8, "students": 620, "progress": 65, "avgXP": 2100,
                "courses": {
                    "webdev": {
                        "name": "Web Development",
                        "batches": {
                            "webdev-2026-jan": {"name": "Jan-Apr 2026", "colleges": 3, "students": 260, "progress": 68, "avgXP": 2250}
                        }
                    },
                    "ml": {
                        "name": "Machine Learning",
                        "batches": {
                            "ml-2026-feb": {"name": "Feb-May 2026", "colleges": 3, "students": 220, "progress": 59, "avgXP": 1950}
                        }
                    },
                    "cloud": {
                        "name": "Cloud Computing",
                        "batches": {
                            "cloud-2026-mar": {"name": "Mar-Jun 2026", "colleges": 2, "students": 140, "progress": 69, "avgXP": 2050}
                        }
                    }
                }
            },
            "ilw": {
                "colleges": 3, "students": 180, "progress": 88, "avgXP": 3400,
                "courses": {
                    "linux_adv": {
                        "name": "Linux Administration",
                        "batches": {
                            "linux-2026-jul": {"name": "Jul-Oct 2026", "colleges": 1, "students": 90, "progress": 91, "avgXP": 3500}
                        }
                    },
                    "cloud_adv": {
                        "name": "Cloud Computing",
                        "batches": {
                            "cloud-2026-mar": {"name": "Mar-Jun 2026", "colleges": 2, "students": 90, "progress": 85, "avgXP": 3250}
                        }
                    }
                }
            }
        },
        "Karnataka": {
            "fdp": {
                "colleges": 3, "students": 210, "progress": 68, "avgXP": 2300,
                "courses": {
                    "linux": {
                        "name": "Linux Administration",
                        "batches": {
                            "linux-2026-jan": {"name": "Jan-Apr 2026", "colleges": 2, "students": 110, "progress": 70, "avgXP": 2400},
                            "linux-2026-jul": {"name": "Jul-Oct 2026", "colleges": 1, "students": 100, "progress": 65, "avgXP": 2200}
                        }
                    },
                    "python": {
                        "name": "Python Programming",
                        "batches": {
                            "python-2026-feb": {"name": "Feb-May 2026", "colleges": 1, "students": 100, "progress": 65, "avgXP": 2200}
                        }
                    }
                }
            },
            "swayam_plus": {
                "colleges": 6, "students": 480, "progress": 58, "avgXP": 1800,
                "courses": {
                    "webdev": {
                        "name": "Web Development",
                        "batches": {
                            "webdev-2026-jan": {"name": "Jan-Apr 2026", "colleges": 3, "students": 210, "progress": 60, "avgXP": 1950}
                        }
                    },
                    "ml": {
                        "name": "Machine Learning",
                        "batches": {
                            "ml-2026-feb": {"name": "Feb-May 2026", "colleges": 2, "students": 160, "progress": 52, "avgXP": 1650}
                        }
                    },
                    "cloud": {
                        "name": "Cloud Computing",
                        "batches": {
                            "cloud-2026-mar": {"name": "Mar-Jun 2026", "colleges": 1, "students": 110, "progress": 61, "avgXP": 1750}
                        }
                    }
                }
            },
            "ilw": {
                "colleges": 2, "students": 130, "progress": 82, "avgXP": 3000,
                "courses": {
                    "linux_adv": {
                        "name": "Linux Administration",
                        "batches": {
                            "linux-2026-jul": {"name": "Jul-Oct 2026", "colleges": 1, "students": 70, "progress": 85, "avgXP": 3200}
                        }
                    },
                    "cloud_adv": {
                        "name": "Cloud Computing",
                        "batches": {
                            "cloud-2026-mar": {"name": "Mar-Jun 2026", "colleges": 1, "students": 60, "progress": 78, "avgXP": 2800}
                        }
                    }
                }
            }
        },
        "Tamil Nadu": {
            "fdp": {
                "colleges": 3, "students": 240, "progress": 74, "avgXP": 2520,
                "courses": {
                    "linux": {
                        "name": "Linux Administration",
                        "batches": {
                            "linux-2026-jan": {"name": "Jan-Apr 2026", "colleges": 1, "students": 120, "progress": 77, "avgXP": 2650},
                            "linux-2026-jul": {"name": "Jul-Oct 2026", "colleges": 2, "students": 120, "progress": 71, "avgXP": 2400}
                        }
                    },
                    "python": {
                        "name": "Python Programming",
                        "batches": {
                            "python-2026-feb": {"name": "Feb-May 2026", "colleges": 2, "students": 120, "progress": 71, "avgXP": 2400}
                        }
                    }
                }
            },
            "swayam_plus": {
                "colleges": 6, "students": 450, "progress": 62, "avgXP": 2000,
                "courses": {
                    "webdev": {
                        "name": "Web Development",
                        "batches": {
                            "webdev-2026-jan": {"name": "Jan-Apr 2026", "colleges": 2, "students": 190, "progress": 65, "avgXP": 2150}
                        }
                    },
                    "ml": {
                        "name": "Machine Learning",
                        "batches": {
                            "ml-2026-feb": {"name": "Feb-May 2026", "colleges": 2, "students": 140, "progress": 56, "avgXP": 1850}
                        }
                    },
                    "cloud": {
                        "name": "Cloud Computing",
                        "batches": {
                            "cloud-2026-mar": {"name": "Mar-Jun 2026", "colleges": 2, "students": 120, "progress": 66, "avgXP": 1950}
                        }
                    }
                }
            },
            "ilw": {
                "colleges": 2, "students": 150, "progress": 86, "avgXP": 3300,
                "courses": {
                    "linux_adv": {
                        "name": "Linux Administration",
                        "batches": {
                            "linux-2026-jul": {"name": "Jul-Oct 2026", "colleges": 1, "students": 80, "progress": 90, "avgXP": 3450}
                        }
                    },
                    "cloud_adv": {
                        "name": "Cloud Computing",
                        "batches": {
                            "cloud-2026-mar": {"name": "Mar-Jun 2026", "colleges": 1, "students": 70, "progress": 83, "avgXP": 3100}
                        }
                    }
                }
            }
        },
        "Delhi": {
            "fdp": {
                "colleges": 2, "students": 120, "progress": 70, "avgXP": 2380,
                "courses": {
                    "linux": {
                        "name": "Linux Administration",
                        "batches": {
                            "linux-2026-jan": {"name": "Jan-Apr 2026", "colleges": 1, "students": 70, "progress": 72, "avgXP": 2450},
                            "linux-2026-jul": {"name": "Jul-Oct 2026", "colleges": 1, "students": 50, "progress": 66, "avgXP": 2300}
                        }
                    },
                    "python": {
                        "name": "Python Programming",
                        "batches": {
                            "python-2026-feb": {"name": "Feb-May 2026", "colleges": 1, "students": 50, "progress": 66, "avgXP": 2300}
                        }
                    }
                }
            },
            "swayam_plus": {
                "colleges": 4, "students": 300, "progress": 60, "avgXP": 1900,
                "courses": {
                    "webdev": {
                        "name": "Web Development",
                        "batches": {
                            "webdev-2026-jan": {"name": "Jan-Apr 2026", "colleges": 2, "students": 140, "progress": 63, "avgXP": 2050}
                        }
                    },
                    "ml": {
                        "name": "Machine Learning",
                        "batches": {
                            "ml-2026-feb": {"name": "Feb-May 2026", "colleges": 1, "students": 80, "progress": 53, "avgXP": 1750}
                        }
                    },
                    "cloud": {
                        "name": "Cloud Computing",
                        "batches": {
                            "cloud-2026-mar": {"name": "Mar-Jun 2026", "colleges": 1, "students": 80, "progress": 63, "avgXP": 1850}
                        }
                    }
                }
            },
            "ilw": {
                "colleges": 1, "students": 60, "progress": 80, "avgXP": 2900,
                "courses": {
                    "linux_adv": {
                        "name": "Linux Administration",
                        "batches": {
                            "linux-2026-jul": {"name": "Jul-Oct 2026", "colleges": 1, "students": 30, "progress": 82, "avgXP": 3100}
                        }
                    },
                    "cloud_adv": {
                        "name": "Cloud Computing",
                        "batches": {
                            "cloud-2026-mar": {"name": "Mar-Jun 2026", "colleges": 0, "students": 30, "progress": 78, "avgXP": 2700}
                        }
                    }
                }
            }
        },
        "Gujarat": {
            "fdp": {
                "colleges": 2, "students": 110, "progress": 71, "avgXP": 2400,
                "courses": {
                    "linux": {
                        "name": "Linux Administration",
                        "batches": {
                            "linux-2026-jan": {"name": "Jan-Apr 2026", "colleges": 1, "students": 60, "progress": 73, "avgXP": 2450},
                            "linux-2026-jul": {"name": "Jul-Oct 2026", "colleges": 1, "students": 50, "progress": 67, "avgXP": 2350}
                        }
                    },
                    "python": {
                        "name": "Python Programming",
                        "batches": {
                            "python-2026-feb": {"name": "Feb-May 2026", "colleges": 1, "students": 50, "progress": 67, "avgXP": 2350}
                        }
                    }
                }
            },
            "swayam_plus": {
                "colleges": 4, "students": 290, "progress": 62, "avgXP": 2000,
                "courses": {
                    "webdev": {
                        "name": "Web Development",
                        "batches": {
                            "webdev-2026-jan": {"name": "Jan-Apr 2026", "colleges": 2, "students": 135, "progress": 65, "avgXP": 2100}
                        }
                    },
                    "ml": {
                        "name": "Machine Learning",
                        "batches": {
                            "ml-2026-feb": {"name": "Feb-May 2026", "colleges": 1, "students": 75, "progress": 55, "avgXP": 1850}
                        }
                    },
                    "cloud": {
                        "name": "Cloud Computing",
                        "batches": {
                            "cloud-2026-mar": {"name": "Mar-Jun 2026", "colleges": 1, "students": 80, "progress": 65, "avgXP": 1950}
                        }
                    }
                }
            },
            "ilw": {
                "colleges": 1, "students": 60, "progress": 82, "avgXP": 3050,
                "courses": {
                    "linux_adv": {
                        "name": "Linux Administration",
                        "batches": {
                            "linux-2026-jul": {"name": "Jul-Oct 2026", "colleges": 1, "students": 30, "progress": 84, "avgXP": 3200}
                        }
                    },
                    "cloud_adv": {
                        "name": "Cloud Computing",
                        "batches": {
                            "cloud-2026-mar": {"name": "Mar-Jun 2026", "colleges": 0, "students": 30, "progress": 80, "avgXP": 2900}
                        }
                    }
                }
            }
        }
    }

    lookup_state = state_key if state_key in data else "all"
    state_data = data[lookup_state]

    if state_key not in data:
        scaled_data = {}
        for prog_id, prog_val in data["all"].items():
            scaled_data[prog_id] = {
                "colleges": max(1, round(prog_val["colleges"] * 0.15)),
                "students": max(10, round(prog_val["students"] * 0.15)),
                "progress": prog_val["progress"],
                "avgXP": prog_val["avgXP"],
                "courses": {}
            }
            for course_id, course_val in prog_val["courses"].items():
                scaled_data[prog_id]["courses"][course_id] = {
                    "name": course_val["name"],
                    "batches": {}
                }
                for batch_id, batch_val in course_val["batches"].items():
                    scaled_data[prog_id]["courses"][course_id]["batches"][batch_id] = {
                        "name": batch_val["name"],
                        "colleges": max(1, round(batch_val["colleges"] * 0.15)),
                        "students": max(5, round(batch_val["students"] * 0.15)),
                        "progress": batch_val["progress"],
                        "avgXP": batch_val["avgXP"]
                    }
        state_data = scaled_data

    programmes_list = []
    colors = {
        "fdp": "hsl(262, 83%, 58%)",
        "swayam_plus": "hsl(221, 83%, 53%)",
        "ilw": "hsl(142, 76%, 36%)"
    }

    for prog_id, prog_val in state_data.items():
        courses_list = []
        for course_id, course_val in prog_val["courses"].items():
            batches_list = []
            for batch_id, batch_val in course_val["batches"].items():
                batches_list.append({
                    "batchId": batch_id,
                    "batchName": batch_val["name"],
                    "metrics": {
                        "colleges": batch_val["colleges"],
                        "students": batch_val["students"],
                        "progress": batch_val["progress"],
                        "avgXP": batch_val["avgXP"]
                    }
                })
            courses_list.append({
                "courseId": course_id,
                "courseName": course_val["name"],
                "batches": batches_list
            })

        programmes_list.append({
            "id": prog_id,
            "name": prog_id.upper() if prog_id != "swayam_plus" else "Swayam Plus",
            "color": colors.get(prog_id, "hsl(200, 80%, 50%)"),
            "metrics": {
                "colleges": prog_val["colleges"],
                "students": prog_val["students"],
                "progress": prog_val["progress"],
                "avgXP": prog_val["avgXP"]
            },
            "courses": courses_list
        })

    return {"programmes": programmes_list}
def generate_deterministic_mock_metrics(prog_id: str, course_id: str, batch_id: str, state: Optional[str] = None):
    # Use ord values of strings to generate a deterministic stable hash/seed
    val_seed = sum(ord(c) for c in (prog_id + course_id + batch_id))
    if state:
        val_seed += sum(ord(c) for c in state)
    
    # Deterministic generation
    colleges = 3 + (val_seed % 10)  # 3 to 12
    students = 70 + ((val_seed * 7) % 330)  # 70 to 400
    progress = 55 + ((val_seed * 13) % 30)  # 55 to 85%
    avg_xp = 1800 + ((val_seed * 19) % 1400)  # 1800 to 3200 XP
    
    # Scale down for state filters
    if state:
        colleges = max(1, round(colleges * 0.25))
        students = max(5, round(students * 0.20))
        progress = max(10, min(100, progress + (val_seed % 7) - 3))
        avg_xp = max(100, avg_xp + (val_seed % 300) - 150)
        
    return {
        "colleges": colleges,
        "students": students,
        "progress": progress,
        "avgXP": avg_xp
    }
