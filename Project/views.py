from django.shortcuts import render
from . models import Project, ProjectGallery

# Create your views here.


def Projects(request,Project_slug):
    try:
        single_project = Project.objects.get(slug=Project_slug)
        brands         = single_project.brands.all()
        client         = single_project.client.all()
        project_cat    = single_project.category.all()




    except Exception as e:
        raise e

    project_gallery    = ProjectGallery.objects.filter(project_id=single_project.id)


    # project_gallery = ProjectGallery.objects.filter(Project_id=single_project.id)

    context = {
        'single_project': single_project,
        'brands'        : brands,
        'client'        : client,
        'project_gallery' : project_gallery,
        'project_cat'   : project_cat,
    }
    return render(request, 'projects/single_project.html', context)

def Projects_completed(request):
    complete_projects = Project.objects.all().filter(completed=True)

    context = {
        'complete_projects' : complete_projects,
    }

    return render(request,'projects/complete_projects.html', context)


def Projects_ongoing(request):
    ongoing_projects = Project.objects.all().filter(ongoing=True)

    context = {
        'ongoing_projects' : ongoing_projects,
    }

    return render(request,'projects/ongoing_projects.html', context)


# def All_Projects(request,Project_slug):
#     all_projects = Project.objects.all()
#
#
#
#     context = {
#         'all_projects' : all_projects,
#
#     }
#
#     return render(request,'projects/all_projects.html', context)


def All_Projects(request):
    all_projects = Project.objects.all()

    # Create a list of dictionaries, each containing project and its gallery images
    projects_with_images = []

    for project in all_projects:
        gallery_images = ProjectGallery.objects.filter(project=project)
        projects_with_images.append({
            'project': project,
            'gallery_images': gallery_images,
        })

    context = {
        'projects_with_images': projects_with_images,
    }

    return render(request, 'projects/all_projects.html', context)
