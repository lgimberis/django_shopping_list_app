
function manageStrikethrough(button){
    hidden = document.getElementById(button.id.replace("button", "hidden"))
    let initial_strikethrough = button.style.getPropertyValue("text-decoration") == "line-through";
    if(initial_strikethrough) {
        // Remove strikethrough
        button.style.setProperty("text-decoration", "");

        button.classList.remove("btn-secondary");
        button.classList.add("btn-primary");
        button.classList.remove("item-remove");
        hidden.value = "keep";
    } else {
        //Add strikethrough
        button.style.setProperty("text-decoration", "line-through");

        button.classList.add("btn-secondary");
        button.classList.remove("btn-primary");
        button.classList.add("item-remove");
        hidden.value = "delete";
    }
    return !initial_strikethrough;
}
